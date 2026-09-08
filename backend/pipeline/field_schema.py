"""
pipeline/field_schema.py — Canonical field-type registry.

Defines, in one place, the expected type for every canonical column name.
All pipeline coercion logic reads from FIELD_TYPES; no per-field-name
conditionals elsewhere.

Types:
  "numeric"          — coerce with pd.to_numeric(errors="coerce"); NaN on failure.
  "date"             — coerce with tolerant pd.to_datetime(errors="coerce").
  "string"           — strip whitespace; keep as-is.
  "categorical"      — keep as-is; unknown values are valid-but-flagged.

Adding or changing a field's type means editing this table only.
"""

# fmt: off
FIELD_TYPES: dict[str, str] = {
    # ── Identity ────────────────────────────────────────────────────────────
    "shipment_id":       "string",

    # ── Dates ───────────────────────────────────────────────────────────────
    "order_date":        "date",
    "expected_delivery": "date",
    "actual_delivery":   "date",

    # ── Geography ───────────────────────────────────────────────────────────
    "origin":            "string",
    "destination":       "string",
    "distance":          "numeric",

    # ── Carrier / parties ───────────────────────────────────────────────────
    "carrier":           "categorical",
    "customer":          "categorical",

    # ── Product ─────────────────────────────────────────────────────────────
    "product":           "categorical",

    # ── Weight ──────────────────────────────────────────────────────────────
    "weight":            "numeric",
    "weight_unit":       "categorical",   # "kg" | "lb" — intentionally a string label

    # ── Quantity ────────────────────────────────────────────────────────────
    "order_quantity":    "numeric",
    "shipped_quantity":  "numeric",

    # ── Cost / invoice ──────────────────────────────────────────────────────
    "cost":              "numeric",
    "contracted_rate":   "numeric",
    "invoice_amount":    "numeric",

    # ── Accessorial — categorical fee *label*, NOT a numeric amount ──────────
    "accessorial":       "categorical",

    # ── Derived (added by cleaning.py, never in raw CSV) ────────────────────
    "status":            "string",
    "is_delayed":        "string",   # handled separately by cleaning.py logic
}
# fmt: on


# Allowlist of values for categorical fields — empty set = "any value accepted".
CATEGORICAL_ALLOWLISTS: dict[str, set[str]] = {
    "weight_unit": {"kg", "lb", "lbs", "kilogram", "kilograms", "pound", "pounds"},
    "accessorial": {
        "none", "fuel surcharge", "detention", "liftgate",
        "residential delivery", "redelivery fee",
    },
}
