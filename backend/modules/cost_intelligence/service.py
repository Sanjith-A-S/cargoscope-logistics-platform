"""
modules/cost_intelligence/service.py — Enhanced cost anomaly detection.

Detection priority:
  1. Contract deviation — if contracted_rate column present in source data.
     Flag where abs(actual_cost - contracted_rate) / contracted_rate > threshold.
     Label: "contract_deviation"
  2. Isolation Forest (existing model) — statistical outlier detection.
     Label: "statistical_isolation_forest"

Also provides lane-level aggregation: OTIF + cost by (origin, destination).
"""
import logging
from typing import Optional

from sqlalchemy import func, Integer
from sqlalchemy.orm import Session

from core.models import Shipment, Route, Order, Invoice, AnomalyReview

logger = logging.getLogger(__name__)

CONTRACT_DEVIATION_THRESHOLD = 0.10  # 10% deviation triggers a flag


def get_cost_anomalies(db: Session, org_id: int, dataset_id: int) -> list:
    """
    Return cost anomalies for the dataset, using contract deviation when
    contracted_rate data is available, otherwise falling back to Isolation Forest.
    """
    rows = (
        db.query(Shipment, Invoice, Route)
        .join(Order, Shipment.order_id == Order.id)
        .join(Invoice, Invoice.order_id == Order.id)
        .join(Route, Shipment.route_id == Route.id)
        .filter(Shipment.dataset_id == dataset_id)
        .all()
    )

    if not rows:
        return []

    # Check if contracted_rate data exists in this dataset
    has_contract_data = any(
        inv.contracted_rate is not None for _, inv, _ in rows
    )

    anomalies = []

    if has_contract_data:
        # Method 1: Contract deviation
        for shipment, invoice, route in rows:
            if invoice.contracted_rate and invoice.cost:
                deviation_pct = abs(invoice.cost - invoice.contracted_rate) / invoice.contracted_rate
                if deviation_pct > CONTRACT_DEVIATION_THRESHOLD:
                    review = (
                        db.query(AnomalyReview)
                        .filter(AnomalyReview.shipment_id == shipment.shipment_id)
                        .first()
                    )
                    anomalies.append({
                        "shipment_id": shipment.shipment_id,
                        "carrier": shipment.carrier,
                        "distance": route.distance if route else 0,
                        "cost": invoice.cost,
                        "contracted_rate": invoice.contracted_rate,
                        "deviation_pct": round(deviation_pct * 100, 1),
                        "base_cost": invoice.base_cost,
                        "accessorial_cost": invoice.accessorial_cost,
                        "detection_method": "contract_deviation",
                        "review_status": review.status if review else "open",
                        "review_notes": review.notes if review else "",
                        "reviewed_at": review.reviewed_at.isoformat() if review and review.reviewed_at else None,
                    })
    else:
        # Method 2: Isolation Forest (existing model)
        try:
            from models.ml_registry import anomaly_detector
            if anomaly_detector.model is None:
                anomaly_detector.train(db, dataset_id=dataset_id, org_id=org_id)

            if anomaly_detector.model is not None:
                raw_anomalies = anomaly_detector.predict(db, dataset_id=dataset_id, org_id=org_id)
                for a in raw_anomalies:
                    sid = a.get("shipment_id", "")
                    review = (
                        db.query(AnomalyReview)
                        .filter(AnomalyReview.shipment_id == sid)
                        .first()
                    )
                    # Try to find carrier from shipment
                    s = db.query(Shipment).filter(Shipment.shipment_id == sid).first()
                    anomalies.append({
                        **a,
                        "carrier": s.carrier if s else None,
                        "contracted_rate": None,
                        "deviation_pct": None,
                        "base_cost": None,
                        "accessorial_cost": None,
                        "detection_method": "statistical_isolation_forest",
                        "review_status": review.status if review else "open",
                        "review_notes": review.notes if review else "",
                        "reviewed_at": review.reviewed_at.isoformat() if review and review.reviewed_at else None,
                    })
        except Exception as e:
            logger.error(f"Anomaly detection failed: {e}")

    return anomalies


def get_lane_summary(db: Session, org_id: int, dataset_id: int) -> list:
    """
    Compute OTIF + average cost aggregated by (origin, destination) lane.
    Sorted by worst on-time rate first (most problematic lanes at top).
    """
    rows = (
        db.query(
            Route.origin,
            Route.destination,
            func.count(Shipment.shipment_id).label("shipment_count"),
            func.avg(Invoice.cost).label("avg_cost"),
            func.sum(
                func.cast(Shipment.is_delayed == False, Integer)
            ).label("on_time_count"),
        )
        .join(Shipment, Shipment.route_id == Route.id)
        .join(Order, Shipment.order_id == Order.id)
        .join(Invoice, Invoice.order_id == Order.id)
        .filter(
            Shipment.dataset_id == dataset_id,
            Shipment.actual_delivery.isnot(None),
        )
        .group_by(Route.origin, Route.destination)
        .all()
    )

    lanes = []
    for r in rows:
        total = r.shipment_count or 0
        on_time = r.on_time_count or 0
        on_time_pct = round(on_time / total * 100, 1) if total > 0 else None
        lanes.append({
            "origin": r.origin,
            "destination": r.destination,
            "shipment_count": total,
            "avg_cost": round(float(r.avg_cost or 0), 2),
            "on_time_pct": on_time_pct,
            "lane": f"{r.origin} → {r.destination}",
        })

    # Sort by worst on-time rate first (None treated as worst)
    lanes.sort(key=lambda x: (x["on_time_pct"] is None, x["on_time_pct"] or 0))
    return lanes
