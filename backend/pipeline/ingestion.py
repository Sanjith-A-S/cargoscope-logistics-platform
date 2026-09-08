"""
pipeline/ingestion.py — CSV → clean DataFrame entry point.

Steps:
  1. Read CSV.
  2. Detect + apply schema mapping (fuzzy column-name resolution).
  3. Validate required columns are present.
  4. Apply column-wise type coercion driven by FIELD_TYPES registry:
       - numeric  → pd.to_numeric(errors="coerce"); warns on bad cells, no crash.
       - date     → tolerant pd.to_datetime(infer_datetime_format=True, errors="coerce").
       - categorical/string → strip whitespace only.
  5. Surface categorical-allowlist violations as warnings (not errors).

Returns (df, mapping, ingestion_warnings) where ingestion_warnings is a list
of human-readable strings describing any coercion issues found.
"""
import logging
from typing import Tuple, Dict, List

import numpy as np
import pandas as pd

from pipeline.schema_detection import detect_schema
from pipeline.schema_mapping import apply_schema_mapping
from pipeline.schema_validation import validate_schema
from pipeline.field_schema import FIELD_TYPES, CATEGORICAL_ALLOWLISTS

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Date-parsing helpers
# ---------------------------------------------------------------------------
_DATE_FORMATS = [
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%d-%m-%Y",
    "%Y/%m/%d",
    "%d %b %Y",
    "%d %B %Y",
    "%b %d, %Y",
]


def _coerce_date_series(series: pd.Series, col: str, warnings: List[str]) -> pd.Series:
    """
    Tolerant date parser: tries infer_datetime_format first, then falls back
    to a list of explicit format strings.  Bad values become NaT (never crash).
    """
    result = pd.to_datetime(series, errors="coerce")
    bad_mask = result.isna() & series.notna() & (series.astype(str).str.strip() != "")
    if bad_mask.any():
        for fmt in _DATE_FORMATS:
            still_bad = result.isna() & bad_mask
            if not still_bad.any():
                break
            parsed = pd.to_datetime(series[still_bad], format=fmt, errors="coerce")
            result[still_bad] = parsed
        # Whatever is still bad after all format attempts → NaT + warn
        final_bad = result.isna() & bad_mask
        if final_bad.any():
            bad_vals = series[final_bad].unique().tolist()[:5]
            warnings.append(
                f"Column '{col}': {final_bad.sum()} value(s) could not be parsed as dates "
                f"→ set to null. Sample: {bad_vals}"
            )
    return result


def _coerce_numeric_series(series: pd.Series, col: str, warnings: List[str]) -> pd.Series:
    """
    Vectorised numeric coercion.  Cells that cannot convert become NaN.
    Reports rows + offending values as a warning (not a crash).
    """
    coerced = pd.to_numeric(series, errors="coerce")
    bad_mask = coerced.isna() & series.notna() & (series.astype(str).str.strip() != "")
    if bad_mask.any():
        bad_vals = series[bad_mask].unique().tolist()[:5]
        warnings.append(
            f"Column '{col}': {bad_mask.sum()} non-numeric value(s) set to null. "
            f"Sample: {bad_vals}"
        )
    return coerced


def _coerce_string_series(series: pd.Series) -> pd.Series:
    """Strip whitespace; leave NaN as NaN."""
    return series.where(series.isna(), series.astype(str).str.strip())


def _coerce_categorical_series(
    series: pd.Series, col: str, warnings: List[str]
) -> pd.Series:
    """
    Categorical: strip whitespace only — do NOT type-coerce.
    Warn if values fall outside the allowlist (if one exists); still accepted.
    """
    result = series.where(series.isna(), series.astype(str).str.strip())
    allowlist = CATEGORICAL_ALLOWLISTS.get(col)
    if allowlist:
        out_of_set = result.dropna()
        out_of_set = out_of_set[~out_of_set.str.lower().isin(allowlist)]
        if not out_of_set.empty:
            unique_vals = out_of_set.unique().tolist()[:5]
            warnings.append(
                f"Column '{col}': {len(out_of_set)} row(s) contain values outside the "
                f"expected set — treated as valid. Sample: {unique_vals}"
            )
    return result


# ---------------------------------------------------------------------------
# Column-wise coercion dispatcher
# ---------------------------------------------------------------------------
def apply_type_coercion(
    df: pd.DataFrame, warnings: List[str]
) -> Tuple[pd.DataFrame, Dict[str, str]]:
    """
    Apply FIELD_TYPES coercion rules column-wise to df.
    Returns (coerced_df, {col: applied_type}).
    Columns not in FIELD_TYPES are left untouched.
    """
    coerced_types: Dict[str, str] = {}
    df = df.copy()

    for col in df.columns:
        field_type = FIELD_TYPES.get(col)
        if field_type is None:
            # Unknown/extra column — leave as-is
            continue

        if field_type == "numeric":
            df[col] = _coerce_numeric_series(df[col], col, warnings)
            coerced_types[col] = "numeric"

        elif field_type == "date":
            df[col] = _coerce_date_series(df[col], col, warnings)
            coerced_types[col] = "date"

        elif field_type == "string":
            df[col] = _coerce_string_series(df[col])
            coerced_types[col] = "string"

        elif field_type == "categorical":
            df[col] = _coerce_categorical_series(df[col], col, warnings)
            coerced_types[col] = "categorical"

    return df, coerced_types


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def ingest_dataset(
    file_path_or_buffer, dataset_name: str = "Unknown"
) -> Tuple[pd.DataFrame, Dict[str, str], List[str]]:
    """
    Ingest a CSV dataset into a typed pandas DataFrame.

    Returns
    -------
    df       : cleaned, type-coerced DataFrame with canonical column names.
    mapping  : {original_col → canonical_col} dict (only renamed cols).
    warnings : list of human-readable coercion-warning strings.
    """
    try:
        df = pd.read_csv(file_path_or_buffer)
    except Exception as exc:
        raise ValueError(f"Failed to read CSV: {exc}") from exc

    original_columns = list(df.columns)

    # 1. Schema detection + mapping
    mapping = detect_schema(original_columns)
    df = apply_schema_mapping(df, mapping)

    mapped_columns = list(df.columns)

    # 2. Required-column validation
    df = validate_schema(df)

    # 3. Column-wise type coercion (vectorised, non-crashing)
    warnings: List[str] = []
    df, _applied = apply_type_coercion(df, warnings)

    initial_rows = len(df)
    logger.info("Dataset Name: %s", dataset_name)
    logger.info("Detected columns: %s", original_columns)
    logger.info("Mapped columns: %s", mapped_columns)
    logger.info("Rows processed: %d", initial_rows)
    if warnings:
        for w in warnings:
            logger.warning("Coercion warning — %s", w)

    return df, mapping, warnings
