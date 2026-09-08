"""
modules/transit_model/service.py — Weight-Adjusted Transit Time Model.

Historical/statistical model only. Models how a third-party carrier has
historically performed on shipments of a given weight and distance.
No live routing, no vehicle dispatch.

Fallback chain (per spec §5):
  1. Bucket median — (carrier × distance_band × weight_band), requires ≥ BUCKET_MIN_SAMPLES
  2. Per-carrier linear regression — transit_time ~ distance + weight, requires ≥ CARRIER_MIN_SAMPLES
  3. Global (all-carrier) linear regression

Always returns the method used + confidence level so the UI can show
a confidence indicator instead of false precision.
"""
import logging
from typing import Optional

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from sklearn.linear_model import LinearRegression

from core.models import Shipment, Route, Order

logger = logging.getLogger(__name__)

# ─── Config constants (tune without touching logic) ───────────────────────────
BUCKET_MIN_SAMPLES = 15   # bucket median requires at least this many shipments
CARRIER_MIN_SAMPLES = 30  # per-carrier regression requires at least this many


# ─── In-memory model store (keyed by dataset_id) ─────────────────────────────
_transit_models: dict = {}  # dataset_id → TransitModelState


class TransitModelState:
    """Holds the fitted bucketing + regression artefacts for one dataset."""

    def __init__(self):
        self.df: Optional[pd.DataFrame] = None          # historical data
        self.global_model: Optional[LinearRegression] = None
        self.carrier_models: dict = {}                   # carrier → LinearRegression
        self.distance_bins: Optional[pd.IntervalIndex] = None
        self.weight_bins: Optional[pd.IntervalIndex] = None
        self.bucket_stats: Optional[pd.DataFrame] = None


def _load_completed_shipments(db: Session, org_id: int, dataset_id: int) -> pd.DataFrame:
    """Query completed shipments with weight and distance for the given dataset."""
    rows = (
        db.query(
            Shipment.shipment_id,
            Shipment.carrier,
            Shipment.expected_delivery,
            Shipment.actual_delivery,
            Shipment.weight_kg,
            Shipment.order_id,
            Route.distance,
            Order.order_date,
        )
        .join(Route, Shipment.route_id == Route.id)
        .join(Order, Shipment.order_id == Order.id)
        .filter(
            Shipment.dataset_id == dataset_id,
            Shipment.actual_delivery.isnot(None),
            Route.distance > 0,
        )
        .all()
    )

    if not rows:
        return pd.DataFrame()

    records = []
    for r in rows:
        if r.actual_delivery and r.order_date:
            transit_days = (r.actual_delivery - r.order_date).total_seconds() / 86400.0
            records.append({
                "carrier": r.carrier or "Unknown",
                "distance": r.distance or 0.0,
                "weight_kg": r.weight_kg or 0.0,
                "transit_days": max(transit_days, 0),
            })

    return pd.DataFrame(records)


def retrain_transit_model(db: Session, org_id: int, dataset_id: int) -> None:
    """Fit the transit model artefacts for a dataset. Called after each upload."""
    df = _load_completed_shipments(db, org_id, dataset_id)
    if df.empty or len(df) < 5:
        logger.info(f"Transit model: not enough data for dataset {dataset_id} (need ≥5 completed shipments)")
        return

    state = TransitModelState()
    state.df = df

    # ── Quantile bins (terciles) for distance and weight ─────────────────────
    try:
        _, state.distance_bins = pd.qcut(df["distance"], q=3, retbins=True, duplicates="drop")
        _, state.weight_bins   = pd.qcut(df["weight_kg"].clip(lower=0.001), q=3, retbins=True, duplicates="drop")
    except Exception:
        state.distance_bins = np.array([0, 1000, 5000, np.inf])
        state.weight_bins   = np.array([0, 200, 600, np.inf])

    # ── Label each row with its band ─────────────────────────────────────────
    df["dist_band"]   = pd.cut(df["distance"],              bins=state.distance_bins, labels=False, include_lowest=True)
    df["weight_band"] = pd.cut(df["weight_kg"].clip(lower=0), bins=state.weight_bins, labels=False, include_lowest=True)

    # ── Bucket statistics ─────────────────────────────────────────────────────
    state.bucket_stats = (
        df.groupby(["carrier", "dist_band", "weight_band"])["transit_days"]
        .agg(["median", "count"])
        .reset_index()
        .rename(columns={"median": "median_days", "count": "n"})
    )

    # ── Per-carrier regressions ───────────────────────────────────────────────
    for carrier, grp in df.groupby("carrier"):
        if len(grp) >= CARRIER_MIN_SAMPLES:
            X = grp[["distance", "weight_kg"]].values
            y = grp["transit_days"].values
            m = LinearRegression().fit(X, y)
            state.carrier_models[carrier] = m

    # ── Global regression ─────────────────────────────────────────────────────
    if len(df) >= 5:
        X = df[["distance", "weight_kg"]].values
        y = df["transit_days"].values
        state.global_model = LinearRegression().fit(X, y)

    _transit_models[dataset_id] = state
    logger.info(f"Transit model retrained for dataset {dataset_id}: {len(df)} samples")


def _get_band(value: float, bins) -> Optional[int]:
    """Return the bin index for a value, or None if out of range."""
    try:
        labels = pd.cut([value], bins=bins, labels=False, include_lowest=True)
        v = labels[0]
        return int(v) if not pd.isna(v) else None
    except Exception:
        return None


def expected_transit_time(
    carrier: str,
    distance: float,
    weight_kg: float,
    dataset_id: int,
    db: Session,
    org_id: int,
) -> dict:
    """
    Predict expected transit time for a shipment.

    Returns:
    {
        "expected_days": float,
        "method": "bucket_median" | "carrier_regression" | "global_regression" | "fallback",
        "confidence": "high" | "medium" | "low",
        "sample_count": int,
    }
    """
    state: Optional[TransitModelState] = _transit_models.get(dataset_id)

    # If model hasn't been trained yet, try to train it now
    if state is None:
        try:
            retrain_transit_model(db=db, org_id=org_id, dataset_id=dataset_id)
            state = _transit_models.get(dataset_id)
        except Exception:
            pass

    if state is None or state.df is None:
        return {"expected_days": 5.0, "method": "fallback", "confidence": "low", "sample_count": 0}

    # ── 1. Bucket median ──────────────────────────────────────────────────────
    if state.bucket_stats is not None and state.distance_bins is not None and state.weight_bins is not None:
        db_idx = _get_band(distance, state.distance_bins)
        wb_idx = _get_band(max(weight_kg, 0), state.weight_bins)

        if db_idx is not None and wb_idx is not None:
            match = state.bucket_stats[
                (state.bucket_stats["carrier"] == carrier) &
                (state.bucket_stats["dist_band"] == db_idx) &
                (state.bucket_stats["weight_band"] == wb_idx)
            ]
            if not match.empty and match.iloc[0]["n"] >= BUCKET_MIN_SAMPLES:
                return {
                    "expected_days": round(float(match.iloc[0]["median_days"]), 2),
                    "method": "bucket_median",
                    "confidence": "high",
                    "sample_count": int(match.iloc[0]["n"]),
                }

    # ── 2. Per-carrier regression ─────────────────────────────────────────────
    if carrier in state.carrier_models:
        m = state.carrier_models[carrier]
        pred = m.predict([[distance, weight_kg]])[0]
        n = len(state.df[state.df["carrier"] == carrier])
        return {
            "expected_days": round(max(float(pred), 0.5), 2),
            "method": "carrier_regression",
            "confidence": "medium",
            "sample_count": n,
        }

    # ── 3. Global regression ──────────────────────────────────────────────────
    if state.global_model is not None:
        pred = state.global_model.predict([[distance, weight_kg]])[0]
        return {
            "expected_days": round(max(float(pred), 0.5), 2),
            "method": "global_regression",
            "confidence": "low",
            "sample_count": len(state.df),
        }

    return {"expected_days": 5.0, "method": "fallback", "confidence": "low", "sample_count": 0}
