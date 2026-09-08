"""
api/analytics.py — Analytics endpoints (dataset-scoped).

Changes from baseline:
  - All endpoints accept dataset_id query param (required when org has data).
  - Queries are filtered by org_id + dataset_id (multi-tenancy boundary).
  - get_shipments() filters by dataset_id when provided.
  - Returns 409 with code=NO_DATASET when no dataset found.
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional

from database.db import get_db
from core.auth import get_current_user
from analytics.analytics_engine import AnalyticsEngine
from database.models import Shipment, Order, Customer, Route, Dataset

router = APIRouter(tags=["Analytics"], dependencies=[Depends(get_current_user)])


def _resolve_dataset_id(dataset_id: Optional[int], org_id: int, db: Session) -> Optional[int]:
    """
    If dataset_id not supplied, try to auto-resolve the most-recently-updated
    dataset for this org. Returns None if org has no datasets yet.
    """
    if dataset_id is not None:
        # Validate ownership
        ds = db.query(Dataset).filter(
            Dataset.id == dataset_id, Dataset.org_id == org_id
        ).first()
        if not ds:
            raise HTTPException(
                status_code=403, detail="Dataset does not belong to your organisation."
            )
        return dataset_id

    # Auto-resolve latest
    ds = (
        db.query(Dataset)
        .filter(Dataset.org_id == org_id)
        .order_by(Dataset.last_updated_at.desc())
        .first()
    )
    return ds.id if ds else None


def _no_data_response():
    raise HTTPException(
        status_code=409,
        detail={"code": "NO_DATASET", "message": "No dataset available. Please upload data first."},
    )


@router.get("/dashboard")
async def get_dashboard_data(
    dataset_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = current_user["org_id"]
    resolved_id = _resolve_dataset_id(dataset_id, org_id, db)
    if resolved_id is None:
        _no_data_response()

    engine = AnalyticsEngine(db, dataset_id=resolved_id)

    kpis = engine.get_dashboard_kpis()
    costs_by_carrier = engine.get_costs_by_carrier()
    top_routes = engine.get_top_routes(10)
    partner_performance = engine.get_partner_performance()
    shipment_volume_trend = engine.get_shipment_volume_trend()
    dynamic_insights = engine.generate_dynamic_insights()

    return {
        "kpis": kpis,
        "dataset_id": resolved_id,
        "charts": {
            "costs_by_carrier": costs_by_carrier,
            "top_routes": top_routes,
            "partner_performance": partner_performance,
            "shipment_volume_trend": shipment_volume_trend,
        },
        "insights": dynamic_insights,
    }


@router.get("/shipments")
async def get_shipments(
    page: int = 1,
    limit: int = 100,
    search: Optional[str] = None,
    carrier: Optional[str] = None,
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    status: Optional[str] = None,
    sort_by: Optional[str] = "shipment_id",
    sort_desc: bool = False,
    dataset_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = current_user["org_id"]
    resolved_id = _resolve_dataset_id(dataset_id, org_id, db)
    if resolved_id is None:
        _no_data_response()

    skip = (page - 1) * limit

    query = (
        db.query(
            Shipment.shipment_id,
            Shipment.carrier,
            Shipment.status,
            Shipment.is_delayed,
            Route.origin,
            Route.destination,
            Customer.name.label("customer"),
        )
        .join(Route, Shipment.route_id == Route.id)
        .join(Order, Shipment.order_id == Order.id)
        .join(Customer, Order.customer_id == Customer.id)
        .filter(Shipment.dataset_id == resolved_id)
    )

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Shipment.shipment_id.ilike(search_term))
            | (Shipment.carrier.ilike(search_term))
            | (Shipment.status.ilike(search_term))
            | (Route.origin.ilike(search_term))
            | (Route.destination.ilike(search_term))
            | (Customer.name.ilike(search_term))
        )

    if carrier:
        query = query.filter(Shipment.carrier.ilike(f"%{carrier}%"))
    if origin:
        query = query.filter(Route.origin.ilike(f"%{origin}%"))
    if destination:
        query = query.filter(Route.destination.ilike(f"%{destination}%"))
    if status:
        query = query.filter(Shipment.status.ilike(f"%{status}%"))

    total_records = query.count()

    if sort_by == "customer":
        sort_col = Customer.name
    elif sort_by == "origin":
        sort_col = Route.origin
    elif sort_by == "destination":
        sort_col = Route.destination
    else:
        sort_col = getattr(Shipment, sort_by, Shipment.shipment_id)

    if sort_desc:
        query = query.order_by(sort_col.desc())
    else:
        query = query.order_by(sort_col.asc())

    results = query.offset(skip).limit(limit).all()
    data = [r._asdict() for r in results]

    return {
        "data": data,
        "dataset_id": resolved_id,
        "pagination": {
            "total": total_records,
            "page": page,
            "limit": limit,
            "total_pages": (total_records + limit - 1) // limit,
        },
    }


@router.get("/carrier-ranking")
async def get_carrier_ranking(
    dataset_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = current_user["org_id"]
    resolved_id = _resolve_dataset_id(dataset_id, org_id, db)
    if resolved_id is None:
        _no_data_response()
    engine = AnalyticsEngine(db, dataset_id=resolved_id)
    rankings = engine.get_carrier_ranking()
    return {"data": rankings, "dataset_id": resolved_id}


@router.get("/carrier/{carrier}/routes")
async def get_carrier_route_ranking(
    carrier: str,
    dataset_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = current_user["org_id"]
    resolved_id = _resolve_dataset_id(dataset_id, org_id, db)
    if resolved_id is None:
        _no_data_response()
    engine = AnalyticsEngine(db, dataset_id=resolved_id)
    rankings = engine.get_carrier_route_ranking(carrier)
    return {"data": rankings, "dataset_id": resolved_id}
