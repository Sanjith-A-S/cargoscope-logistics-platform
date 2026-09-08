# CargoScope Sample Datasets

This directory contains synthetic Indian freight and trade logistics datasets specifically crafted to test and demonstrate CargoScope's end-to-end ingestion, schema harmonization, weight-adjusted transit modeling, OTIF tracking, and multi-dataset lifecycle management.

---

## Files Overview

| File | Records | Primary Purpose | Key Characteristics |
|---|---|---|---|
| `indian_logistics_primary.csv` | ~1,000 rows | **Primary Baseline Dataset** | Full historical freight records across major Indian transport lanes (Mumbai, Delhi, Bangalore, Chennai, Kolkata, Indore, etc.) with 7 major carriers. Includes weights, quantities, contracted rates, and accessorial fees. |
| `indian_logistics_update.csv` | ~180 rows | **Update & Merge Testing** | Contains incremental shipment records and follow-on delivery updates. Used to test dataset continuation, incremental deduplication, and re-running transit models on existing datasets. |
| `indian_logistics_new_dataset.csv` | ~400 rows | **Dataset Isolation & Switching** | An independent, distinct shipment slice. Used to verify multi-dataset workspace isolation, active dataset switching, and ensuring metrics do not leak across datasets. |
| `indian_logistics_corrupt.csv` | ~500 rows | **Resilience & Schema Ingestion Testing** | Contains non-standard column headers (`consignment_num`, `freight_price`, `origin_city`), dirty date formats, mixed weight units (`kg`/`lb`), and missing fields to validate fuzzy schema mapping and type coercion. |
| `sample_trade_data.csv` | ~1,000 rows | **Legacy Sample Dataset** | General sample trade logistics dataset for baseline regression tests. |

---

## Schema & Column Reference

All CSVs contain (or map to) the following canonical schema fields:

- `shipment_id` *(String)*: Unique tracking identifier (e.g. `SFX260100001`, `BLD260400007`).
- `customer` *(String)*: B2B shipper or receiving client (e.g. `Malabar Spices & Foods`, `Aravalli Industrial Corp`).
- `origin` *(String)*: Source dispatch city/hub (e.g. `Indore`, `Mumbai`, `Delhi`).
- `destination` *(String)*: Delivery destination city/hub (e.g. `Nagpur`, `Surat`, `Kochi`).
- `order_date` *(Date/Timestamp)*: ISO-formatted order or pickup date.
- `carrier` *(String)*: 3PL freight carrier name (e.g. `Safexpress`, `Blue Dart`, `Delhivery`, `DTDC`, `Gati-KWE`, `TCI Express`, `XpressBees`).
- `cost` *(Numeric)*: Billed freight invoice amount (INR / currency units).
- `product` *(String)*: Product category (e.g. `FMCG Bulk Pack`, `Steel Fabrication Parts`, `Auto Components`).
- `distance` *(Numeric)*: Route transit distance in kilometers.
- `expected_delivery` *(Date/Timestamp)*: Carrier SLA delivery commitment date.
- `actual_delivery` *(Date/Timestamp)*: Actual delivery timestamp (empty/null if currently in-transit).
- `weight` *(Numeric)*: Cargo payload weight.
- `weight_unit` *(String)*: Unit of weight measure (`kg` or `lb` — automatically normalized to kg).
- `order_quantity` *(Integer)*: Number of units ordered.
- `shipped_quantity` *(Integer)*: Number of units fulfilled (used alongside delivery dates for OTIF evaluation).
- `contracted_rate` *(Numeric)*: Baseline contractual agreed rate.
- `accessorial` *(String)*: Accessorial surcharge type (e.g. `Detention`, `Liftgate`, `Residential Delivery`, `Fuel Surcharge`, `None`).

---

## Recommended Quickstart Flow

1. Log into CargoScope.
2. Go to **Settings** (`/settings`) → Click **Upload CSV**.
3. Select `datasets/indian_logistics_primary.csv` and create a new dataset named `"Q1 Logistics Baseline"`.
4. Explore the **Live Risk Queue**, **Carrier Performance**, and **Anomaly Review** tabs.
5. In Settings, upload `datasets/indian_logistics_new_dataset.csv` as a new dataset named `"West Coast Operations"`.
6. Switch active datasets and observe complete tenant-scoped analytical isolation.
