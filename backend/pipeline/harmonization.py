"""
pipeline/harmonization.py — Cleans and stores a DataFrame into the relational DB.

Design notes
============
- By the time this function is called, ingestion.py has already applied
  column-wise type coercion driven by FIELD_TYPES:
    • numeric columns  → float64 / NaN   (never a plain string)
    • date columns     → pd.Timestamp / NaT
    • categorical cols → stripped string (e.g. accessorial = "Redelivery Fee")

  Therefore we do NOT re-coerce types here. We only do safe sentinel
  checks (is None / is NaN) and hand values to SQLAlchemy.

- `accessorial` in the source CSV is a categorical *label*, not a numeric
  amount. The Invoice.accessorial_cost DB column stores a float, so the
  column's label is recorded separately in the ingestion summary and
  accessorial_cost is left NULL. If a future schema adds a string label
  column to Invoice, update this mapping here.

- Accepts dataset_id and org_id; tags every record for multi-tenancy.
- Normalises weight to kg (lb → kg conversion).
- Synthetic dedup key: sha256(carrier+origin+destination+order_date+customer)
  when shipment_id is missing/null.
- Returns a HarmonizationResult named-tuple with row counts, coercion
  warnings forwarded from ingestion, and a per-column type summary.
"""
import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

import pandas as pd
from sqlalchemy.orm import Session

from core.models import Customer, Invoice, Order, PipelineLog, Route, Shipment

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result dataclass returned to upload.py
# ---------------------------------------------------------------------------
@dataclass
class HarmonizationResult:
    inserted: int = 0
    skipped_duplicates: int = 0
    coercion_warnings: List[str] = field(default_factory=list)
    # rows that had at least one NaN in a mandatory numeric field
    rows_with_null_numerics: int = 0
    # Sample of (row_index, column, original_value) for warning display
    null_numeric_samples: List[dict] = field(default_factory=list)
    categorical_columns_kept_as_string: List[str] = field(default_factory=list)
    numeric_columns_coerced: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def _normalize_weight_kg(weight, unit) -> Optional[float]:
    """Convert weight to kg. Returns None if weight is NaN/None."""
    if weight is None or (isinstance(weight, float) and pd.isna(weight)):
        return None
    try:
        w = float(weight)
    except (ValueError, TypeError):
        return None
    if unit and str(unit).lower().strip() in ("lb", "lbs", "pound", "pounds"):
        return round(w * 0.453592, 4)
    return round(w, 4)  # assume kg


def _safe_float(val) -> Optional[float]:
    """Return float(val) or None; never raises."""
    if val is None:
        return None
    try:
        if pd.isna(val):
            return None
    except Exception:
        pass
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _safe_date(val) -> Optional[datetime]:
    """
    Safely convert a pd.Timestamp / datetime / NaT / None to Python datetime.
    Ingestion already parsed these; this is a safety net only.
    """
    if val is None:
        return None
    try:
        if pd.isna(val):
            return None
    except Exception:
        pass
    if isinstance(val, pd.Timestamp):
        return None if pd.isna(val) else val.to_pydatetime()
    if isinstance(val, datetime):
        return val
    if isinstance(val, str):
        val_str = val.strip()
        if not val_str or val_str.lower() in ("nat", "nan", "none", "null"):
            return None
        try:
            return pd.to_datetime(val_str).to_pydatetime()
        except Exception:
            return None
    try:
        dt = pd.to_datetime(val)
        return None if pd.isna(dt) else dt.to_pydatetime()
    except Exception:
        return None


def _synthetic_shipment_id(row) -> str:
    """Build a deterministic dedup key when shipment_id is absent."""
    parts = [
        str(row.get("carrier", "") or ""),
        str(row.get("origin", "") or ""),
        str(row.get("destination", "") or ""),
        str(row.get("order_date", "") or ""),
        str(row.get("customer", "") or ""),
    ]
    raw = "|".join(parts).encode("utf-8")
    return "syn_" + hashlib.sha256(raw).hexdigest()[:24]


# ---------------------------------------------------------------------------
# Public function
# ---------------------------------------------------------------------------
def harmonize_and_store(
    df: pd.DataFrame,
    db: Session,
    dataset_id: Optional[int] = None,
    org_id: Optional[int] = None,
    coercion_warnings: Optional[List[str]] = None,
) -> HarmonizationResult:
    """
    Persist a cleaned, typed DataFrame to the relational database.

    Parameters
    ----------
    df                : typed DataFrame from ingestion + cleaning.
    db                : SQLAlchemy session.
    dataset_id        : FK to associate all rows with.
    org_id            : FK for multi-tenancy.
    coercion_warnings : warnings list from ingestion.py, forwarded into result.

    Returns
    -------
    HarmonizationResult with inserted/skipped counts and warning summaries.
    """
    result = HarmonizationResult(
        coercion_warnings=list(coercion_warnings or []),
    )

    # Derive summary metadata from the DataFrame's actual dtypes/columns
    from pipeline.field_schema import FIELD_TYPES
    for col in df.columns:
        ft = FIELD_TYPES.get(col)
        if ft == "numeric":
            result.numeric_columns_coerced.append(col)
        elif ft == "categorical":
            result.categorical_columns_kept_as_string.append(col)

    df = df.where(pd.notnull(df), None)

    customer_cache: dict = {}
    route_cache: dict = {}

    # Check if shipment_id is genuinely present
    has_natural_id = (
        "shipment_id" in df.columns
        and df["shipment_id"].notna().any()
        and (df["shipment_id"].astype(str).str.strip() != "").any()
    )

    if not has_natural_id:
        try:
            log = PipelineLog(
                timestamp=datetime.utcnow(),
                event_type="Warning",
                description=(
                    "No natural shipment_id column found — using synthetic hash key. "
                    "Deduplication may be imprecise if key fields change between uploads."
                ),
                org_id=org_id,
                dataset_id=dataset_id,
            )
            db.add(log)
            db.flush()
        except Exception:
            pass

    # Pre-fetch existing shipment IDs scoped to this dataset for O(1) deduplication
    existing_query = db.query(Shipment.shipment_id)
    if dataset_id is not None:
        existing_query = existing_query.filter(Shipment.dataset_id == dataset_id)
    existing_ids = {row.shipment_id for row in existing_query.all()}

    for _, row in df.iterrows():
        # ── Resolve shipment ID ───────────────────────────────────────────
        sid = str(row.get("shipment_id") or "").strip()
        if not sid:
            sid = _synthetic_shipment_id(row)

        # Skip duplicates (idempotent ingestion scoped to dataset)
        if sid in existing_ids:
            result.skipped_duplicates += 1
            continue
        existing_ids.add(sid)

        # ── Customer ─────────────────────────────────────────────────────
        cust_name = str(row.get("customer") or "Unknown Customer").strip()
        cache_key = (cust_name, dataset_id)
        if cache_key not in customer_cache:
            customer = (
                db.query(Customer)
                .filter(
                    Customer.name == cust_name,
                    Customer.dataset_id == dataset_id,
                )
                .first()
            )
            if not customer:
                customer = Customer(name=cust_name, dataset_id=dataset_id)
                db.add(customer)
                db.flush()
            customer_cache[cache_key] = customer.id

        cust_id = customer_cache[cache_key]

        # ── Route ─────────────────────────────────────────────────────────
        origin = str(row.get("origin") or "Unknown").strip()
        destination = str(row.get("destination") or "Unknown").strip()
        route_key = (origin, destination, dataset_id)

        if route_key not in route_cache:
            route = (
                db.query(Route)
                .filter(
                    Route.origin == origin,
                    Route.destination == destination,
                    Route.dataset_id == dataset_id,
                )
                .first()
            )
            if not route:
                dist = _safe_float(row.get("distance"))
                route = Route(
                    origin=origin,
                    destination=destination,
                    distance=dist if dist is not None else 0.0,
                    dataset_id=dataset_id,
                )
                db.add(route)
                db.flush()
            route_cache[route_key] = route.id

        route_id = route_cache[route_key]

        # ── Order ─────────────────────────────────────────────────────────
        order = Order(
            customer_id=cust_id,
            order_date=_safe_date(row.get("order_date")),
            product=str(row.get("product") or "Unknown").strip(),
            dataset_id=dataset_id,
        )
        db.add(order)
        db.flush()

        # ── Weight normalisation ──────────────────────────────────────────
        raw_weight = _safe_float(row.get("weight"))
        # weight_unit is categorical string — read it directly, no float()
        weight_unit_raw = row.get("weight_unit")
        weight_unit = (
            str(weight_unit_raw).strip().lower()
            if weight_unit_raw is not None
            else "kg"
        ) or "kg"
        weight_kg = _normalize_weight_kg(raw_weight, weight_unit)

        # ── Shipment ──────────────────────────────────────────────────────
        oq = _safe_float(row.get("order_quantity"))
        sq = _safe_float(row.get("shipped_quantity"))
        delayed_val = row.get("is_delayed")
        is_delayed = (
            bool(delayed_val)
            if (delayed_val is not None and not pd.isna(delayed_val))
            else False
        )

        shipment = Shipment(
            shipment_id=sid,
            order_id=order.id,
            route_id=route_id,
            carrier=str(row.get("carrier") or "Unknown").strip(),
            expected_delivery=_safe_date(row.get("expected_delivery")),
            actual_delivery=_safe_date(row.get("actual_delivery")),
            status=str(row.get("status") or "Unknown").strip(),
            is_delayed=is_delayed,
            dataset_id=dataset_id,
            weight=raw_weight,
            weight_unit=weight_unit or None,
            weight_kg=weight_kg,
            order_quantity=oq,
            shipped_quantity=sq,
        )
        db.add(shipment)

        # ── Invoice ───────────────────────────────────────────────────────
        cost = _safe_float(row.get("cost"))
        contracted = _safe_float(row.get("contracted_rate"))
        inv_amt = _safe_float(row.get("invoice_amount"))

        # `accessorial` is a categorical *label* (e.g. "Redelivery Fee"), not
        # a numeric amount.  Store cost=0 for now; accessorial_cost stays NULL.
        # A future schema addition can store the label in a String column.
        invoice = Invoice(
            order_id=order.id,
            amount=inv_amt if inv_amt is not None else 0.0,
            cost=cost if cost is not None else 0.0,
            dataset_id=dataset_id,
            contracted_rate=contracted,
            accessorial_cost=None,   # label not coercible to float — stored as NULL
        )
        db.add(invoice)
        result.inserted += 1

    db.commit()
    return result
