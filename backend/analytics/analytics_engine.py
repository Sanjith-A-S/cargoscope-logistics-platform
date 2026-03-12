from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from database.models import Shipment, Invoice, Route, Order, Customer

class AnalyticsEngine:
    def __init__(self, db: Session):
        self.db = db

    def get_dashboard_kpis(self):
        total_shipments = self.db.query(Shipment).count()
        delayed_shipments = self.db.query(Shipment).filter(Shipment.is_delayed == True).count()
        
        avg_cost_result = self.db.query(func.avg(Invoice.cost)).scalar()
        average_cost = round(avg_cost_result, 2) if avg_cost_result else 0.0
        
        active_routes_count = self.db.query(Route).count()
        
        return {
            "total_shipments": total_shipments,
            "delayed_shipments": delayed_shipments,
            "average_cost": average_cost,
            "active_routes": active_routes_count
        }

    def get_costs_by_carrier(self):
        results = (
            self.db.query(
                Shipment.carrier,
                func.avg(Invoice.cost).label('avg_cost')
            )
            .join(Order, Shipment.order_id == Order.id)
            .join(Invoice, Invoice.order_id == Order.id)
            .group_by(Shipment.carrier)
            .all()
        )
        return [{"carrier": r.carrier, "average_cost": round(r.avg_cost, 2)} for r in results if r.carrier]

    def get_top_routes(self, limit=5):
        results = (
            self.db.query(
                Route.origin,
                Route.destination,
                func.count(Shipment.shipment_id).label('shipment_count')
            )
            .join(Shipment, Shipment.route_id == Route.id)
            .group_by(Route.id)
            .order_by(desc('shipment_count'))
            .limit(limit)
            .all()
        )
        return [{"origin": r.origin, "destination": r.destination, "count": r.shipment_count} for r in results]

    def get_partner_performance(self):
        """
        Calculate on_time_delivery_rate by carrier
        """
        total_by_carrier = (
            self.db.query(Shipment.carrier, func.count(Shipment.shipment_id).label('total'))
            .group_by(Shipment.carrier)
            .subquery()
        )
        
        delayed_by_carrier = (
            self.db.query(Shipment.carrier, func.count(Shipment.shipment_id).label('delayed'))
            .filter(Shipment.is_delayed == True)
            .group_by(Shipment.carrier)
            .subquery()
        )
        
        results = (
            self.db.query(
                total_by_carrier.c.carrier,
                total_by_carrier.c.total,
                func.coalesce(delayed_by_carrier.c.delayed, 0).label('delayed')
            )
            .outerjoin(delayed_by_carrier, total_by_carrier.c.carrier == delayed_by_carrier.c.carrier)
            .all()
        )
        
        performance = []
        for r in results:
            if r.carrier:
                on_time_rate = ((r.total - r.delayed) / r.total) * 100 if r.total > 0 else 0
                performance.append({
                    "carrier": r.carrier,
                    "total_shipments": r.total,
                    "on_time_rate": round(on_time_rate, 2)
                })
                
        return sorted(performance, key=lambda x: x['on_time_rate'], reverse=True)
