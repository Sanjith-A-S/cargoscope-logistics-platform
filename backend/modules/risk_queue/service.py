"""
modules/risk_queue/service.py — Live Risk Queue scorer.

Scores every in-transit shipment (actual_delivery IS NULL) for a dataset,
combining the weight-adjusted transit model (Module 5) with the existing
delay predictor for a severity score.

Severity = projected_overrun_days × confidence_weight
  confidence_weight: bucket_median=1.0, carrier_regression=0.7, global_regression=0.4, fallback=0.2

Each row includes a plain-English reason phrase explaining the flag.
"""
import logging
from datetime import datetime, date
from typing import Optional

from sqlalchemy.orm import Session

from core.models import Shipment, Route, Order, Invoice
from modules.transit_model.service import expected_transit_time

logger = logging.getLogger(__name__)

CONFIDENCE_WEIGHTS = {
    "bucket_median":      1.0,
    "carrier_regression": 0.7,
    "global_regression":  0.4,
    "fallback":           0.2,
}

RISK_LEVELS = {
    "high":   lambda s: s >= 2.0,
    "medium": lambda s: 0.5 <= s < 2.0,
    "low":    lambda s: s < 0.5,
}


def _risk_level(severity: float) -> str:
    if severity >= 2.0:
        return "high"
    if severity >= 0.5:
        return "medium"
    return "low"


def _build_reason(
    carrier: str,
    weight_kg: Optional[float],
    transit_result: dict,
    overrun_days: float,
) -> str:
    method = transit_result.get("method", "fallback")
    expected = transit_result.get("expected_days", 0)
    n = transit_result.get("sample_count", 0)
    w = round(weight_kg or 0, 1)

    if method == "bucket_median" and n > 0:
        return (
            f"{w}kg on {carrier} — historically {round(overrun_days, 1)} day(s) "
            f"slower than quoted for this weight and distance band "
            f"(based on {n} similar shipments)."
        )
    elif method == "carrier_regression":
        return (
            f"{carrier} is running {round(overrun_days, 1)} day(s) behind "
            f"the expected {round(expected, 1)}-day transit time for "
            f"this distance and weight ({w}kg)."
        )
    elif method == "global_regression":
        return (
            f"Shipment is {round(overrun_days, 1)} day(s) beyond the network-wide "
            f"average for {round(expected, 1)} days — {carrier} has limited "
            f"history for this lane so confidence is low."
        )
    else:
        return (
            f"Shipment has been in transit longer than expected "
            f"({round(overrun_days, 1)} day(s) over estimate). "
            f"Insufficient carrier history for a precise benchmark."
        )


def score_in_transit_shipments(db: Session, org_id: int, dataset_id: int) -> list:
    """
    Score all in-transit shipments for a dataset by severity.
    Returns a list sorted by severity descending (most urgent first).
    """
    rows = (
        db.query(Shipment, Route, Order)
        .join(Route, Shipment.route_id == Route.id)
        .join(Order, Shipment.order_id == Order.id)
        .filter(
            Shipment.dataset_id == dataset_id,
            Shipment.actual_delivery.is_(None),
        )
        .all()
    )

    today = datetime.utcnow()
    results = []

    # Also load delay predictor for secondary probability signal
    delay_predictor = None
    try:
        from models.ml_registry import delay_predictor as dp
        delay_predictor = dp
    except Exception:
        pass

    for shipment, route, order in rows:
        if not order.order_date:
            continue

        days_in_transit = (today - order.order_date).total_seconds() / 86400.0

        transit_result = expected_transit_time(
            carrier=shipment.carrier or "Unknown",
            distance=route.distance if route else 0.0,
            weight_kg=shipment.weight_kg or 0.0,
            dataset_id=dataset_id,
            db=db,
            org_id=org_id,
        )

        expected_days = transit_result["expected_days"]
        overrun_days = days_in_transit - expected_days
        confidence_weight = CONFIDENCE_WEIGHTS.get(transit_result["method"], 0.2)
        severity = max(overrun_days * confidence_weight, 0)

        # Secondary delay probability from logistic regression
        delay_prob = None
        if delay_predictor and delay_predictor.model is not None:
            try:
                from models.ml_registry import delay_predictor as dp
                delay_prob = dp.predict_delay_prob(
                    distance=route.distance or 0,
                    carrier=shipment.carrier or "Unknown",
                    origin=route.origin or "Unknown",
                    destination=route.destination or "Unknown",
                    cost=0.0,
                )
            except Exception:
                pass

        reason = _build_reason(
            carrier=shipment.carrier or "Unknown",
            weight_kg=shipment.weight_kg,
            transit_result=transit_result,
            overrun_days=overrun_days,
        )

        results.append({
            "shipment_id": shipment.shipment_id,
            "carrier": shipment.carrier or "Unknown",
            "origin": route.origin if route else "",
            "destination": route.destination if route else "",
            "order_date": order.order_date.isoformat() if order.order_date else None,
            "days_in_transit": round(days_in_transit, 1),
            "expected_transit_days": expected_days,
            "projected_overrun_days": round(overrun_days, 1),
            "severity_score": round(severity, 3),
            "severity_level": _risk_level(severity),
            "confidence": transit_result.get("confidence", "low"),
            "transit_method": transit_result.get("method", "fallback"),
            "delay_probability": round(delay_prob, 3) if delay_prob is not None else None,
            "reason": reason,
            "weight_kg": shipment.weight_kg,
            "status": shipment.status or "In Transit",
        })

    # Sort by severity descending
    results.sort(key=lambda x: x["severity_score"], reverse=True)
    return results
