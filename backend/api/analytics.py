from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.db import get_db
from analytics.analytics_engine import AnalyticsEngine
from database.models import Shipment, Order, Customer, Route
from sqlalchemy import func, desc

router = APIRouter(tags=["Analytics"])

@router.get("/dashboard")
async def get_dashboard_data(db: Session = Depends(get_db)):
    engine = AnalyticsEngine(db)
    
    kpis = engine.get_dashboard_kpis()
    costs_by_carrier = engine.get_costs_by_carrier()
    top_routes = engine.get_top_routes(10)
    partner_performance = engine.get_partner_performance()
    
    return {
        "kpis": kpis,
        "charts": {
            "costs_by_carrier": costs_by_carrier,
            "top_routes": top_routes,
            "partner_performance": partner_performance
        }
    }

@router.get("/shipments")
async def get_shipments(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """ Returns flat shipment data for the Shipment Explorer """
    results = (
        db.query(
            Shipment.shipment_id,
            Shipment.carrier,
            Shipment.status,
            Shipment.is_delayed,
            Route.origin,
            Route.destination,
            Customer.name.label('customer')
        )
        .join(Route, Shipment.route_id == Route.id)
        .join(Order, Shipment.order_id == Order.id)
        .join(Customer, Order.customer_id == Customer.id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [r._asdict() for r in results]
