"""
pipeline/schema_detection.py — fuzzy column header mapper.

Detects non-standard CSV column names and maps them to the platform's
canonical schema. Matching is keyword-based (whole-word / exact token).

Fix: uses whole-word regex matching so that e.g. "weight_unit" does NOT
match the "weight" keyword, and "order_quantity" does NOT accidentally
match the "shipped_quantity" mapping.

Keyword ordering within each list does not matter — the target_col list
ordering in keyword_map_ordered matters: more-specific targets are
checked first so that e.g. "weight_unit" resolves to weight_unit before
the "weight" entry can claim it.
"""
import re
from typing import List, Dict


def _word_match(col_lower: str, keyword: str) -> bool:
    """Return True if `keyword` appears as a whole token in `col_lower`.

    A token boundary is any non-alphanumeric character or string edge.
    Example: 'weight' matches 'weight' and 'gross_weight' but NOT 'weight_unit'.
    """
    pattern = r"(?<![a-z0-9])" + re.escape(keyword) + r"(?![a-z0-9])"
    return bool(re.search(pattern, col_lower))


def detect_schema(columns: List[str]) -> Dict[str, str]:
    """
    Detect dataset column names and suggest platform mappings.
    Returns a mapping dict: {original_col → canonical_col}.

    More-specific / longer targets are listed first so they are matched
    before shorter, overlapping keywords.
    """
    # Order matters: more-specific targets FIRST.
    keyword_map_ordered = [
        # ── Identity ────────────────────────────────────────────────────────
        ("shipment_id",  ["shipment_id", "tracking_id", "consignment_id"]),
        ("order_date",   ["order_date", "created_at"]),
        # ── Delivery dates (more specific before 'arrival') ──────────────────
        ("expected_delivery", [
            "expected_delivery", "expected_date", "eta", "delivery_date",
            "promise_date", "planned_delivery",
        ]),
        ("actual_delivery", [
            "actual_delivery", "actual_date", "delivered_date",
            "arrival_date", "ata", "actual_arrival",
        ]),
        # ── Weight — unit BEFORE bare weight ─────────────────────────────────
        ("weight_unit",  ["weight_unit", "unit_weight", "uom_weight", "wt_unit"]),
        ("weight",       ["weight", "gross_weight", "net_weight", "shipment_weight", "wt"]),
        # ── Quantity — shipped BEFORE order ──────────────────────────────────
        ("shipped_quantity", [
            "shipped_quantity", "qty_shipped", "fulfilled_qty",
            "dispatched", "shipped_qty", "actual_qty",
        ]),
        ("order_quantity", [
            "order_quantity", "qty_ordered", "ordered_qty", "order_qty",
            "quantity", "units",
        ]),
        # ── Cost intelligence ────────────────────────────────────────────────
        ("contracted_rate", [
            "contracted_rate", "tariff_rate", "contract_price", "agreed_rate",
            "expected_cost",
        ]),
        ("accessorial",  ["accessorial", "surcharge_type", "fee_type", "surcharge"]),
        ("cost",         ["cost", "freight_cost", "total_cost", "freight", "price"]),
        # ── Geography ────────────────────────────────────────────────────────
        ("origin",       ["origin", "origin_city", "from_port", "ship_from", "source"]),
        ("destination",  ["destination", "destination_city", "to_port", "ship_to", "arrival"]),
        ("distance",     ["distance", "dist", "km", "miles"]),
        # ── Carrier ──────────────────────────────────────────────────────────
        ("carrier",      ["carrier", "freight_carrier", "shipping_partner", "forwarder"]),
        # ── Misc ─────────────────────────────────────────────────────────────
        ("customer",     ["customer", "buyer", "client"]),
        ("product",      ["product", "item", "sku", "description"]),
        ("shipment_id",  ["shipment", "tracking", "consignment"]),  # fallback aliases
    ]

    mapping = {}
    # Track which canonical targets have already been claimed to avoid
    # multiple source columns collapsing to the same target.
    claimed: dict[str, str] = {}  # target_col → first source col that won it

    for col in columns:
        col_lower = col.lower().strip()
        matched_target = None

        for target_col, keywords in keyword_map_ordered:
            if any(_word_match(col_lower, kw) for kw in keywords):
                matched_target = target_col
                break

        if matched_target and matched_target not in claimed:
            mapping[col] = matched_target
            claimed[matched_target] = col
        else:
            # Either no match, or target already claimed — keep original name.
            mapping[col] = col

    return mapping
