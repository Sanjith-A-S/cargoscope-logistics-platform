"""
pipeline/cleaning.py — Post-ingestion data cleaning.

Assumes ingestion.py has already applied column-wise type coercion, so:
  - Date columns are already pd.Timestamp / NaT.
  - Numeric columns are already float / NaN.
  - Categorical / string columns are already stripped strings.

This module handles:
  1. Deduplication on shipment_id.
  2. Ensuring derived columns exist (status, is_delayed).
  3. Computing is_delayed from delivery dates.
  4. Fuzzy-normalisation of customer names (RapidFuzz).
"""
import logging

import numpy as np
import pandas as pd
from rapidfuzz import fuzz, process

logger = logging.getLogger(__name__)


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean an already-typed DataFrame.

    Returns a cleaned copy; does NOT modify the input in-place.
    """
    df_clean = df.copy()

    # ── 1. Deduplication on shipment_id ─────────────────────────────────────
    before = len(df_clean)
    df_clean = df_clean.drop_duplicates(subset=["shipment_id"])
    dropped = before - len(df_clean)
    if dropped:
        logger.info("Deduplication removed %d duplicate shipment_id row(s).", dropped)

    # ── 2. Ensure required derived columns exist ─────────────────────────────
    if "carrier" in df_clean.columns:
        df_clean["carrier"] = df_clean["carrier"].fillna("Unknown")

    for col in ("status", "is_delayed"):
        if col not in df_clean.columns:
            df_clean[col] = None

    for col in ("actual_delivery", "expected_delivery"):
        if col not in df_clean.columns:
            df_clean[col] = pd.NaT

    # ── 3. Compute is_delayed ────────────────────────────────────────────────
    # Defensively re-coerce date columns in case clean_data is called directly
    # without going through ingestion.py (e.g. tests, acquisition.py).
    for _dc in ("actual_delivery", "expected_delivery", "order_date"):
        if _dc in df_clean.columns and not pd.api.types.is_datetime64_any_dtype(df_clean[_dc]):
            df_clean[_dc] = pd.to_datetime(df_clean[_dc], errors="coerce")

    has_actual = df_clean["actual_delivery"].notna()

    # Strict boundary: actual > expected → delayed; equal → on-time.
    df_clean.loc[has_actual, "is_delayed"] = (
        df_clean.loc[has_actual, "actual_delivery"]
        > df_clean.loc[has_actual, "expected_delivery"]
    )
    df_clean["is_delayed"] = df_clean["is_delayed"].fillna(False).astype(bool)

    # ── 4. Derive status if absent ───────────────────────────────────────────
    status_mask = df_clean["status"].isna()
    df_clean.loc[status_mask & has_actual, "status"] = "Delivered"
    df_clean.loc[status_mask & ~has_actual, "status"] = "In Transit"

    # ── 5. Fuzzy-normalise customer names ────────────────────────────────────
    if "customer" in df_clean.columns:
        unique_customers = df_clean["customer"].dropna().unique().tolist()
        normalized_map: dict[str, str] = {}
        processed: set[str] = set()

        for cust in unique_customers:
            if cust in processed:
                continue
            matches = process.extract(
                cust, unique_customers, scorer=fuzz.WRatio, limit=10
            )
            similar = [m[0] for m in matches if m[1] >= 90]
            if similar:
                representative = min(similar, key=len)
                for s in similar:
                    normalized_map[s] = representative
                    processed.add(s)
            else:
                normalized_map[cust] = cust
                processed.add(cust)

        df_clean["customer"] = (
            df_clean["customer"].map(normalized_map).fillna("Unknown Customer")
        )

    return df_clean
