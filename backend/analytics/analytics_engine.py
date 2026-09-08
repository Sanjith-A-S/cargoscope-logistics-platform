"""
analytics/analytics_engine.py — Core analytics queries.

Changes from baseline:
  - All queries now accept an optional dataset_id parameter for multi-tenancy.
  - get_dashboard_kpis() filters by dataset_id when provided.
  - get_carrier_ranking() adds monthly_trend and weight_band_breakdown fields.
  - All other methods similarly scoped by dataset_id.
"""
from typing import Optional

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, Integer, cast

from database.models import Shipment, Invoice, Route, Order, Customer


class AnalyticsEngine:
    def __init__(self, db: Session, dataset_id: Optional[int] = None):
        self.db = db
        self.dataset_id = dataset_id

    def _shipment_filter(self, query):
        """Apply dataset_id filter when set."""
        if self.dataset_id is not None:
            query = query.filter(Shipment.dataset_id == self.dataset_id)
        return query

    def get_dashboard_kpis(self):
        base = self.db.query(Shipment)
        if self.dataset_id is not None:
            base = base.filter(Shipment.dataset_id == self.dataset_id)

        total_shipments = base.count()
        delayed_shipments = base.filter(Shipment.is_delayed == True).count()

        # Average cost (scoped)
        cost_q = (
            self.db.query(func.avg(Invoice.cost))
            .join(Order, Invoice.order_id == Order.id)
            .join(Shipment, Shipment.order_id == Order.id)
        )
        if self.dataset_id is not None:
            cost_q = cost_q.filter(Shipment.dataset_id == self.dataset_id)
        avg_cost_result = cost_q.scalar()
        average_cost = round(avg_cost_result, 2) if avg_cost_result else 0.0

        # Active routes (scoped)
        route_q = (
            self.db.query(func.count(func.distinct(Shipment.route_id)))
        )
        if self.dataset_id is not None:
            route_q = route_q.filter(Shipment.dataset_id == self.dataset_id)
        active_routes_count = route_q.scalar() or 0

        return {
            "total_shipments": total_shipments,
            "delayed_shipments": delayed_shipments,
            "average_cost": average_cost,
            "active_routes": active_routes_count,
        }

    def get_costs_by_carrier(self):
        q = (
            self.db.query(
                Shipment.carrier,
                func.avg(Invoice.cost).label("avg_cost"),
            )
            .join(Order, Shipment.order_id == Order.id)
            .join(Invoice, Invoice.order_id == Order.id)
        )
        if self.dataset_id is not None:
            q = q.filter(Shipment.dataset_id == self.dataset_id)
        results = q.group_by(Shipment.carrier).all()
        return [
            {"carrier": r.carrier, "average_cost": round(r.avg_cost, 2)}
            for r in results if r.carrier
        ]

    def get_top_routes(self, limit=5):
        q = (
            self.db.query(
                Route.origin,
                Route.destination,
                func.count(Shipment.shipment_id).label("shipment_count"),
            )
            .join(Shipment, Shipment.route_id == Route.id)
        )
        if self.dataset_id is not None:
            q = q.filter(Shipment.dataset_id == self.dataset_id)
        results = (
            q.group_by(Route.id)
            .order_by(desc("shipment_count"))
            .limit(limit)
            .all()
        )
        return [
            {"origin": r.origin, "destination": r.destination, "count": r.shipment_count}
            for r in results
        ]

    def get_partner_performance(self):
        base_filter = (
            [Shipment.dataset_id == self.dataset_id] if self.dataset_id is not None else []
        )

        total_by_carrier = (
            self.db.query(
                Shipment.carrier,
                func.count(Shipment.shipment_id).label("total"),
            )
            .filter(*base_filter)
            .group_by(Shipment.carrier)
            .subquery()
        )

        delayed_by_carrier = (
            self.db.query(
                Shipment.carrier,
                func.count(Shipment.shipment_id).label("delayed"),
            )
            .filter(Shipment.is_delayed == True, *base_filter)
            .group_by(Shipment.carrier)
            .subquery()
        )

        results = (
            self.db.query(
                total_by_carrier.c.carrier,
                total_by_carrier.c.total,
                func.coalesce(delayed_by_carrier.c.delayed, 0).label("delayed"),
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
                    "on_time_rate": round(on_time_rate, 2),
                })
        return performance

    def get_shipment_volume_trend(self):
        q = (
            self.db.query(
                func.strftime("%Y-%m", Order.order_date).label("month"),
                func.count(Shipment.shipment_id).label("volume"),
            )
            .join(Shipment, Shipment.order_id == Order.id)
        )
        if self.dataset_id is not None:
            q = q.filter(Shipment.dataset_id == self.dataset_id)
        results = q.group_by("month").order_by("month").all()
        return [{"date": r.month, "volume": r.volume} for r in results if r.month]

    def get_carrier_ranking(self):
        """
        Carrier ranking with delay rate, avg cost, monthly trend, and weight-band breakdown.
        """
        base_filter = (
            [Shipment.dataset_id == self.dataset_id] if self.dataset_id is not None else []
        )

        total_by_carrier = (
            self.db.query(
                Shipment.carrier,
                func.count(Shipment.shipment_id).label("total"),
            )
            .filter(*base_filter)
            .group_by(Shipment.carrier)
            .subquery()
        )

        delayed_by_carrier = (
            self.db.query(
                Shipment.carrier,
                func.count(Shipment.shipment_id).label("delayed"),
            )
            .filter(Shipment.is_delayed == True, *base_filter)
            .group_by(Shipment.carrier)
            .subquery()
        )

        cost_by_carrier = (
            self.db.query(
                Shipment.carrier,
                func.avg(Invoice.cost).label("avg_cost"),
            )
            .join(Order, Shipment.order_id == Order.id)
            .join(Invoice, Invoice.order_id == Order.id)
            .filter(*base_filter)
            .group_by(Shipment.carrier)
            .subquery()
        )

        results = (
            self.db.query(
                total_by_carrier.c.carrier,
                total_by_carrier.c.total,
                func.coalesce(delayed_by_carrier.c.delayed, 0).label("delayed"),
                func.coalesce(cost_by_carrier.c.avg_cost, 0).label("avg_cost"),
            )
            .outerjoin(delayed_by_carrier, total_by_carrier.c.carrier == delayed_by_carrier.c.carrier)
            .outerjoin(cost_by_carrier, total_by_carrier.c.carrier == cost_by_carrier.c.carrier)
            .all()
        )

        rankings = []
        for r in results:
            if not r.carrier:
                continue
            delay_rate = (r.delayed / r.total * 100) if r.total > 0 else 0

            # Monthly trend (last 12 months)
            monthly_trend = self._get_carrier_monthly_trend(r.carrier)

            # Weight-band breakdown
            weight_band_breakdown = self._get_carrier_weight_bands(r.carrier)

            rankings.append({
                "carrier": r.carrier,
                "total_shipments": r.total,
                "delayed_shipments": r.delayed,
                "delay_rate": round(delay_rate, 2),
                "avg_cost": round(r.avg_cost, 2),
                "monthly_trend": monthly_trend,
                "weight_band_breakdown": weight_band_breakdown,
            })

        sorted_rankings = sorted(rankings, key=lambda x: x["delay_rate"])
        for i, rank in enumerate(sorted_rankings):
            rank["rank"] = i + 1

        return sorted_rankings

    def _get_carrier_monthly_trend(self, carrier: str) -> list:
        """Monthly on-time rate trend for one carrier (last 12 months)."""
        q = (
            self.db.query(
                func.strftime("%Y-%m", Order.order_date).label("month"),
                func.count(Shipment.shipment_id).label("total"),
                func.sum(
                    cast(Shipment.is_delayed == False, Integer)
                ).label("on_time"),
            )
            .join(Order, Shipment.order_id == Order.id)
            .filter(
                func.lower(Shipment.carrier) == func.lower(carrier),
                Shipment.actual_delivery.isnot(None),
            )
        )
        if self.dataset_id is not None:
            q = q.filter(Shipment.dataset_id == self.dataset_id)
        results = (
            q.group_by("month")
            .order_by("month")
            .limit(12)
            .all()
        )
        return [
            {
                "month": r.month,
                "on_time_pct": round((r.on_time or 0) / r.total * 100, 1) if r.total > 0 else None,
                "delay_rate": round(((r.total - (r.on_time or 0)) / r.total) * 100, 1) if r.total > 0 else None,
                "total": r.total,
            }
            for r in results if r.month
        ]

    def _get_carrier_weight_bands(self, carrier: str) -> list:
        """Weight-band breakdown for one carrier. Uses dataset's weight_kg distribution."""
        # Pull all shipments with weight for this carrier + dataset
        q = (
            self.db.query(
                Shipment.weight_kg,
                Shipment.is_delayed,
                Order.order_date,
                Shipment.actual_delivery,
            )
            .join(Order, Shipment.order_id == Order.id)
            .filter(
                func.lower(Shipment.carrier) == func.lower(carrier),
                Shipment.weight_kg.isnot(None),
                Shipment.actual_delivery.isnot(None),
            )
        )
        if self.dataset_id is not None:
            q = q.filter(Shipment.dataset_id == self.dataset_id)
        rows = q.all()

        if not rows:
            return []

        df = pd.DataFrame([
            {
                "weight_kg": r.weight_kg,
                "is_delayed": r.is_delayed,
                "transit_days": (
                    (r.actual_delivery - r.order_date).total_seconds() / 86400
                    if r.actual_delivery and r.order_date else None
                ),
            }
            for r in rows
        ]).dropna()

        if df.empty or len(df) < 3:
            return []

        try:
            df["band"], bins = pd.qcut(
                df["weight_kg"], q=3, retbins=True, duplicates="drop"
            )
        except Exception:
            bins = [df["weight_kg"].min(), df["weight_kg"].median(), df["weight_kg"].max()]
            df["band"] = pd.cut(df["weight_kg"], bins=bins, labels=False, include_lowest=True)

        results = []
        for band_val, grp in df.groupby("band"):
            on_time = len(grp[grp["is_delayed"] == False])
            total = len(grp)
            idx = int(band_val) if hasattr(band_val, '__int__') else 0

            # Build label from bin edges
            try:
                lo = round(bins[idx], 1)
                hi = round(bins[idx + 1], 1)
                label = f"{lo}–{hi} kg"
            except Exception:
                label = f"Band {idx + 1}"

            results.append({
                "weight_band": label,
                "shipment_count": total,
                "on_time_pct": round(on_time / total * 100, 1) if total > 0 else None,
                "avg_transit_days": round(float(grp["transit_days"].mean()), 1),
            })

        return results

    def get_carrier_route_ranking(self, carrier: str):
        base_filter = (
            [Shipment.dataset_id == self.dataset_id] if self.dataset_id is not None else []
        )

        total_by_route = (
            self.db.query(
                Route.origin,
                Route.destination,
                func.count(Shipment.shipment_id).label("total"),
            )
            .join(Shipment, Shipment.route_id == Route.id)
            .filter(func.lower(Shipment.carrier) == func.lower(carrier), *base_filter)
            .group_by(Route.origin, Route.destination)
            .subquery()
        )

        delayed_by_route = (
            self.db.query(
                Route.origin,
                Route.destination,
                func.count(Shipment.shipment_id).label("delayed"),
            )
            .join(Shipment, Shipment.route_id == Route.id)
            .filter(
                func.lower(Shipment.carrier) == func.lower(carrier),
                Shipment.is_delayed == True,
                *base_filter,
            )
            .group_by(Route.origin, Route.destination)
            .subquery()
        )

        cost_by_route = (
            self.db.query(
                Route.origin,
                Route.destination,
                func.avg(Invoice.cost).label("avg_cost"),
            )
            .join(Shipment, Shipment.route_id == Route.id)
            .join(Order, Shipment.order_id == Order.id)
            .join(Invoice, Invoice.order_id == Order.id)
            .filter(func.lower(Shipment.carrier) == func.lower(carrier), *base_filter)
            .group_by(Route.origin, Route.destination)
            .subquery()
        )

        results = (
            self.db.query(
                total_by_route.c.origin,
                total_by_route.c.destination,
                total_by_route.c.total,
                func.coalesce(delayed_by_route.c.delayed, 0).label("delayed"),
                func.coalesce(cost_by_route.c.avg_cost, 0).label("avg_cost"),
            )
            .outerjoin(
                delayed_by_route,
                (total_by_route.c.origin == delayed_by_route.c.origin)
                & (total_by_route.c.destination == delayed_by_route.c.destination),
            )
            .outerjoin(
                cost_by_route,
                (total_by_route.c.origin == cost_by_route.c.origin)
                & (total_by_route.c.destination == cost_by_route.c.destination),
            )
            .all()
        )

        rankings = []
        for r in results:
            if r.origin and r.destination:
                delay_rate = (r.delayed / r.total * 100) if r.total > 0 else 0
                rankings.append({
                    "route": f"{r.origin} → {r.destination}",
                    "total_shipments": r.total,
                    "delayed_shipments": r.delayed,
                    "delay_rate": round(delay_rate, 2),
                    "avg_cost": round(r.avg_cost, 2),
                })

        sorted_rankings = sorted(rankings, key=lambda x: x["delay_rate"])
        for i, rank in enumerate(sorted_rankings):
            rank["rank"] = i + 1
        return sorted_rankings

    def generate_dynamic_insights(self):
        insights = []

        carrier_rankings = self.get_carrier_ranking()
        if carrier_rankings:
            worst_carrier = max(carrier_rankings, key=lambda x: x["delay_rate"])
            insights.append({
                "type": "warning",
                "title": "Highest Delay Carrier",
                "message": (
                    f"{worst_carrier['carrier']} has the highest delay rate at "
                    f"{worst_carrier['delay_rate']}% across {worst_carrier['total_shipments']} shipments."
                ),
            })
            best_carrier = min(carrier_rankings, key=lambda x: x["delay_rate"])
            insights.append({
                "type": "success",
                "title": "Top Performing Carrier",
                "message": (
                    f"{best_carrier['carrier']} is performing best with only a "
                    f"{best_carrier['delay_rate']}% delay rate."
                ),
            })

        top_routes = self.get_top_routes(1)
        if top_routes:
            top = top_routes[0]
            insights.append({
                "type": "info",
                "title": "Most Active Route",
                "message": (
                    f"The route from {top['origin']} to {top['destination']} "
                    f"has the highest volume with {top['count']} shipments."
                ),
            })

        avg_cost_q = (
            self.db.query(func.avg(Invoice.cost))
            .join(Order, Invoice.order_id == Order.id)
            .join(Shipment, Shipment.order_id == Order.id)
        )
        if self.dataset_id is not None:
            avg_cost_q = avg_cost_q.filter(Shipment.dataset_id == self.dataset_id)
        avg_cost = avg_cost_q.scalar()

        if avg_cost:
            high_cost_q = (
                self.db.query(func.count(Invoice.id))
                .join(Order, Invoice.order_id == Order.id)
                .join(Shipment, Shipment.order_id == Order.id)
                .filter(Invoice.cost > avg_cost * 1.5)
            )
            if self.dataset_id is not None:
                high_cost_q = high_cost_q.filter(Shipment.dataset_id == self.dataset_id)
            high_cost_shipments = high_cost_q.scalar()
            if high_cost_shipments > 0:
                insights.append({
                    "type": "error",
                    "title": "Cost Anomalies Detected",
                    "message": (
                        f"Detected {high_cost_shipments} shipments with costs "
                        f"significantly above the average of ${avg_cost:.2f}."
                    ),
                })

        return insights
