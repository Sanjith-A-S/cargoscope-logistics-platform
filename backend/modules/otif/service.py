"""
modules/otif/service.py — OTIF (On-Time In-Full) computation engine.

on_time  = actual_delivery <= weight-adjusted expected transit time (Module 5)
in_full  = shipped_quantity >= order_quantity  (if both columns present)
otif     = on_time AND in_full

If quantity data is absent, falls back to on_time_only mode and sets
has_quantity_data = False so the UI can display the correct label.
"""
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from core.models import Shipment, Route, Order, Invoice
from modules.transit_model.service import expected_transit_time

logger = logging.getLogger(__name__)


def _compute_on_time(shipment: Shipment, route, order, db: Session, org_id: int, dataset_id: int) -> Optional[bool]:
    """Return True if on-time, False if late, None if can't determine."""
    if not shipment.actual_delivery or not order.order_date:
        return None

    transit_result = expected_transit_time(
        carrier=shipment.carrier or "Unknown",
        distance=route.distance if route else 0.0,
        weight_kg=shipment.weight_kg or 0.0,
        dataset_id=dataset_id,
        db=db,
        org_id=org_id,
    )

    expected_days = transit_result["expected_days"]
    from datetime import timedelta
    deadline = order.order_date + timedelta(days=expected_days)
    return shipment.actual_delivery <= deadline


def compute_otif(db: Session, org_id: int, dataset_id: int) -> dict:
    """
    Compute OTIF for all delivered shipments in the dataset.
    Returns structured result including trend by month and breakdown by carrier.
    """
    # Validate dataset belongs to this org
    from core.models import Dataset
    ds = db.query(Dataset).filter(
        Dataset.id == dataset_id,
        Dataset.org_id == org_id,
    ).first()
    if not ds:
        return _empty_otif()

    rows = (
        db.query(Shipment, Route, Order)
        .join(Route, Shipment.route_id == Route.id)
        .join(Order, Shipment.order_id == Order.id)
        .filter(
            Shipment.dataset_id == dataset_id,
            Shipment.actual_delivery.isnot(None),
        )
        .all()
    )

    if not rows:
        return _empty_otif()

    # Determine if quantity data is available
    has_quantity_data = any(
        s.order_quantity is not None and s.shipped_quantity is not None
        for s, _, _ in rows
    )

    total = 0
    on_time_count = 0
    in_full_count = 0
    otif_count = 0

    monthly: dict = {}    # "YYYY-MM" → {on_time, in_full, otif, total}
    by_carrier: dict = {} # carrier → {on_time, in_full, otif, total}

    for shipment, route, order in rows:
        on_time = _compute_on_time(shipment, route, order, db, org_id, dataset_id)
        if on_time is None:
            continue

        if has_quantity_data:
            oq = shipment.order_quantity
            sq = shipment.shipped_quantity
            if oq is not None and sq is not None:
                in_full = sq >= oq
            else:
                in_full = None
        else:
            in_full = None

        is_otif = on_time and (in_full if in_full is not None else True) if has_quantity_data else None

        total += 1
        if on_time:
            on_time_count += 1
        if in_full:
            in_full_count += 1
        if is_otif:
            otif_count += 1

        # Monthly bucketing
        if order.order_date:
            month_key = order.order_date.strftime("%Y-%m")
            if month_key not in monthly:
                monthly[month_key] = {"on_time": 0, "in_full": 0, "otif": 0, "total": 0}
            monthly[month_key]["total"] += 1
            if on_time:
                monthly[month_key]["on_time"] += 1
            if in_full:
                monthly[month_key]["in_full"] += 1
            if is_otif:
                monthly[month_key]["otif"] += 1

        # Carrier bucketing
        carrier = shipment.carrier or "Unknown"
        if carrier not in by_carrier:
            by_carrier[carrier] = {"on_time": 0, "in_full": 0, "otif": 0, "total": 0}
        by_carrier[carrier]["total"] += 1
        if on_time:
            by_carrier[carrier]["on_time"] += 1
        if in_full:
            by_carrier[carrier]["in_full"] += 1
        if is_otif:
            by_carrier[carrier]["otif"] += 1

    def _pct(num, den):
        return round(num / den * 100, 1) if den > 0 else None

    mode = "otif" if has_quantity_data else "on_time_only"

    by_month = [
        {
            "month": k,
            "on_time_pct": _pct(v["on_time"], v["total"]),
            "in_full_pct": _pct(v["in_full"], v["total"]) if has_quantity_data else None,
            "otif_pct": _pct(v["otif"], v["total"]) if has_quantity_data else None,
        }
        for k, v in sorted(monthly.items())
    ]

    carrier_breakdown = [
        {
            "carrier": c,
            "on_time_pct": _pct(v["on_time"], v["total"]),
            "in_full_pct": _pct(v["in_full"], v["total"]) if has_quantity_data else None,
            "otif_pct": _pct(v["otif"], v["total"]) if has_quantity_data else None,
            "shipment_count": v["total"],
        }
        for c, v in sorted(by_carrier.items(), key=lambda x: -x[1]["total"])
    ]

    return {
        "otif_pct": _pct(otif_count, total) if has_quantity_data else None,
        "on_time_pct": _pct(on_time_count, total),
        "in_full_pct": _pct(in_full_count, total) if has_quantity_data else None,
        "has_quantity_data": has_quantity_data,
        "total_shipments": total,
        "mode": mode,
        "by_month": by_month,
        "by_carrier": carrier_breakdown,
    }


def _empty_otif() -> dict:
    return {
        "otif_pct": None,
        "on_time_pct": None,
        "in_full_pct": None,
        "has_quantity_data": False,
        "total_shipments": 0,
        "mode": "on_time_only",
        "by_month": [],
        "by_carrier": [],
    }
