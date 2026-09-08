# Trade Intelligence Platform — Full Documentation

> **Target User:** Ops/Logistics Managers who need to know what shipments are late, why, and which carriers are underperforming — without any data engineering background.

---

## 1. What This Platform Does

The Trade Intelligence Platform is a **single-operator logistics analytics tool** that ingests raw CSV shipment exports, cleans and normalises the data automatically, stores it in a relational database, trains two machine-learning models on it, and surfaces the results as interactive dashboards, rankings, anomaly queues, and a predictive "what-if" simulator — all behind a secure login.

**In one sentence:** Upload a messy CSV → get instant visibility into delays, carrier performance, cost anomalies, and delay risk scores.

---

## 2. User-Facing App Flow (End-to-End)

### Step 1 — Login

The user navigates to `http://localhost:5173` and is immediately redirected to `/login`. They enter credentials (`admin` / `tradeops2024`). On success, a JWT Bearer token is stored in `sessionStorage` and the user is routed to the Dashboard. Every subsequent API call carries this token automatically via an Axios interceptor.

### Step 2 — Upload Data (Settings Screen)

`/settings` → Upload CSV button.

The user picks a `.csv` file from their machine. The file is sent to the backend as `multipart/form-data`. The platform **auto-detects the column schema** — you do not need to rename your columns first. Non-standard headers like `tracking_number`, `buyer`, `from_port` are fuzzy-matched to the canonical schema.

**Required columns (or auto-mapped equivalents):**

| Canonical Name | Also Accepts |
|---|---|
| `shipment_id` | `tracking`, `consignment`, `tracking_number` |
| `customer` | `buyer`, `client` |
| `origin` | `source`, `from_port`, `origin_city` |
| `destination` | `to_port`, `arrival`, `destination_city` |
| `order_date` | `created_at` |
| `carrier` | `shipping_partner` |
| `cost` | `freight`, `price`, `freight_cost` |

After upload, both ML models retrain automatically on the new data. A sample dataset is included at `datasets/sample_trade_data.csv`.

### Step 3 — Dashboard (`/`)

The main landing page after login. Shows 4 KPI cards at the top:

- **Total Shipments** — total records in DB
- **Delayed Shipments** — count where `actual_delivery > expected_delivery`
- **Average Freight Cost** — mean of all invoiced costs
- **Active Routes** — number of unique origin→destination pairs

Below the KPIs are four charts:

1. **Shipment Volume Trend** — month-by-month bar chart showing order volume
2. **Costs by Carrier** — average freight cost per carrier (bar chart)
3. **Partner Performance** — on-time delivery rate per carrier (horizontal bar)
4. **Top Routes** — highest-volume origin→destination pairs

At the bottom: **Dynamic Insights** — auto-generated text cards flagging the worst delay carrier, the best carrier, the busiest route, and cost anomaly count.

### Step 4 — Shipments Screen (`/shipments`)

A full paginated table of every shipment in the database. Features:

- **Global search** — searches across shipment ID, carrier, status, origin, destination, customer simultaneously
- **Column filters** — filter by carrier, origin, destination, or status independently
- **Sorting** — click any column header
- **Pagination** — 100 rows per page by default
- **Delayed badge** — rows with `is_delayed = true` are visually highlighted

### Step 5 — Carrier Performance (`/carriers`)

A ranked table of all carriers sorted by delay rate (ascending — lowest delay = rank #1). For each carrier:

- Total shipments, delayed count, delay rate (%)
- Average freight cost
- **Drill-down:** click any carrier → see route-level breakdown for that carrier (which specific routes are causing the delays)

### Step 6 — Anomaly Review (`/anomalies`)

A queue of **cost anomalies** flagged by the Isolation Forest ML model. Each row shows:

- Shipment ID, distance, flagged cost
- Current review status: `open` / `investigated` / `dismissed`

The operator clicks a shipment and marks it investigated or dismissed with optional notes. This state persists to the `anomaly_reviews` table and survives page reloads.

### Step 7 — Delay Predictor (`/api/insights/predict`)

The platform exposes a **"what-if" delay risk scorer**. The operator provides:

- Carrier name, origin, destination, distance (km), cost (USD)

The model returns:

- `delay_probability` — a 0.0–1.0 float
- `risk_level` — `low` (<0.35), `medium` (0.35–0.65), or `high` (≥0.65)
- `top_features` — the 3 input features contributing most to the score and whether they increase or decrease risk

### Step 8 — Data Activity (`/sources/monitor`)

A log of every pipeline event: file received, schema detected, rows cleaned, storage complete, ML training complete, or errors. Useful for auditing what was processed and when.

---

## 3. Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Browser (React SPA)                  │
│  Login → Dashboard → Shipments → Carriers → Anomalies  │
│  Vite + React Router + Axios (JWT interceptor)          │
└───────────────────────┬────────────────────────────────┘
                        │ HTTP/JSON (JWT Bearer)
                        ▼
┌─────────────────────────────────────────────────────────┐
│               FastAPI Backend (Python)                  │
│  Uvicorn ASGI server — port 8000                        │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐  │
│  │  /upload │  │/analytics│  │/insights │  │/auth   │  │
│  └────┬─────┘  └─────┬────┘  └────┬─────┘  └────────┘  │
│       │              │             │                     │
│  ┌────▼─────────┐    │    ┌────────▼──────┐             │
│  │   Pipeline   │    │    │   ML Models   │             │
│  │  (3 stages)  │    │    │  Delay Pred.  │             │
│  └────┬─────────┘    │    │  Anomaly Det. │             │
│       │              │    └───────────────┘             │
│  ┌────▼──────────────▼──────────────────────────────┐   │
│  │           Analytics Engine (SQLAlchemy)           │   │
│  └────────────────────┬──────────────────────────────┘   │
└───────────────────────┼────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│                 SQLite Database                         │
│  datasets/trade_data.db                                 │
│  Tables: customers, routes, orders,                     │
│          shipments, invoices,                           │
│          anomaly_reviews, pipeline_logs                 │
└─────────────────────────────────────────────────────────┘
```

---

## 4. Data Storage — Schema & Relationships

The database is **SQLite** (`datasets/trade_data.db`), managed by **SQLAlchemy ORM**. It is a deliberately normalised relational schema, not a flat CSV mirror.

### Entity-Relationship Diagram

```
customers (id PK, name UNIQUE)
    │ 1
    │ ∞
orders (id PK, customer_id FK, order_date, product)
    │ 1                    │ 1
    │ ∞                    │ 1
shipments                 invoices
(shipment_id PK,         (id PK, order_id FK,
 order_id FK,             amount FLOAT,
 route_id FK,             cost FLOAT)
 carrier,
 expected_delivery,
 actual_delivery,
 status,
 is_delayed BOOL)
    │ ∞
    │ 1
routes (id PK, origin, destination, distance)

anomaly_reviews (id PK, shipment_id UNIQUE,
                 status, notes, reviewed_at)

pipeline_logs (id PK, timestamp, event_type, description)
```

### Key design decisions

- **Customers are deduplicated** — RapidFuzz (WRatio ≥ 90) collapses `"Apple"` and `"Apple Inc."` into one record before storage.
- **Routes are deduplicated** — a `(origin, destination)` pair is created once and reused across shipments.
- **Idempotent ingestion** — re-uploading the same file is safe; shipments already in the DB are skipped by `shipment_id`.
- **AnomalyReview is separate** — ML anomaly flags live outside the main shipment table so they can be updated without affecting source data.

---

## 5. In-Depth Technical Flow: Data Upload → Visual Report

### Stage 1: HTTP Ingest — `POST /api/upload`

```
User selects CSV file in Settings UI
        │
        ▼
Axios sends multipart/form-data with JWT Bearer token
        │
        ▼
FastAPI validates: JWT ✓, file extension .csv ✓
        │
        ▼  [upload.py]
PipelineLog: "Upload — CSV file received: filename (N bytes)"
```

### Stage 2: Ingestion Pipeline — `pipeline/ingestion.py`

```
pd.read_csv(file_bytes)  →  raw DataFrame
        │
        ▼  [schema_detection.py]
detect_schema(columns)
  - Iterates each column header (case-insensitive substring match)
  - "tracking_number" → contains "tracking"  → maps to "shipment_id"
  - "from_port"       → contains "from_port" → maps to "origin"
  - "freight_cost"    → contains "freight"   → maps to "cost"
  - Unmatched columns pass through unchanged
  - Returns: Dict[original_col → canonical_col]
        │
        ▼  [schema_mapping.py]
apply_schema_mapping(df, mapping)
  - df.rename(columns=mapping)
  - DataFrame now has canonical column names
        │
        ▼  [schema_validation.py]
validate_schema(df)
  - Required: shipment_id, customer, origin, destination, order_date
  - Raises SchemaValidationError (lists missing fields) on failure
  - Returns validated DataFrame
        │
        ▼
PipelineLog: "Processing — Schema detected and mapped: N rows"
```

### Stage 3: Cleaning — `pipeline/cleaning.py`

```
drop_duplicates(subset=['shipment_id'])
  → exact duplicate shipment IDs removed
        │
        ▼
Date parsing: order_date, expected_delivery, actual_delivery
  → pd.to_datetime(errors='coerce')  — invalid dates become NaT
        │
        ▼
Missing carrier → filled with "Unknown"
        │
        ▼
is_delayed calculation (strict boundary rule):
  is_delayed = (actual_delivery > expected_delivery)
  # actual == expected  = on-time  (not delayed)
  # actual > expected   = delayed
  # NaN actual_delivery = False    (in-transit, outcome unknown)
        │
        ▼
status derivation (rows where status is missing):
  has actual_delivery  → "Delivered"
  no  actual_delivery  → "In Transit"
        │
        ▼
Customer name normalisation via RapidFuzz WRatio ≥ 90:
  - Cluster similar names: "Apple" / "Apple Inc." / "APPLE" → shortest wins
  - Apply normalised_map across entire customer column
  - Prevents duplicate customer records in the database
        │
        ▼
PipelineLog: "Processing — Data cleaned: N records after deduplication"
```

### Stage 4: Harmonisation & Storage — `pipeline/harmonization.py`

```
For each row in cleaned DataFrame:
  │
  ├─ SKIP if Shipment.shipment_id already exists in DB  [idempotency]
  │
  ├─ CUSTOMER
  │    Lookup: SELECT * FROM customers WHERE name = ?
  │    Miss?  INSERT INTO customers (name) → db.flush() → get id
  │    Cache  customer_id in memory dict (avoids repeat queries)
  │
  ├─ ROUTE
  │    Lookup: SELECT * FROM routes WHERE origin = ? AND destination = ?
  │    Miss?  INSERT INTO routes (origin, destination, distance)
  │    Cache  route_id in memory dict
  │
  ├─ ORDER
  │    Always INSERT (one CSV row = one order)
  │    Fields: customer_id FK, order_date, product
  │
  ├─ SHIPMENT
  │    INSERT with shipment_id PK, order_id FK, route_id FK
  │    Fields: carrier, expected_delivery, actual_delivery,
  │            status, is_delayed
  │
  └─ INVOICE
       INSERT with order_id FK
       Fields: amount (invoice_amount), cost

db.commit()  →  entire batch persisted atomically to SQLite
        │
        ▼
PipelineLog: "Ingestion — Records harmonized and stored in database"
```

### Stage 5: ML Training — triggered automatically after every upload

#### Delay Predictor (`models/delay_prediction.py`)

```
Query:
  JOIN shipments ↔ routes ↔ orders ↔ invoices
  WHERE actual_delivery IS NOT NULL   (completed shipments only)
  Minimum 50 rows required

Features:   distance, carrier (encoded), origin (encoded),
            destination (encoded), cost
Label:      is_delayed → int (0 or 1)

Preprocessing:
  LabelEncoder per categorical column [carrier, origin, destination]
  Encodes string categories → integers

Model Pipeline:
  StandardScaler → LogisticRegression(max_iter=500)
  80% train / 20% test split (random_state=42)

Persist:
  joblib.dump({ model, label_encoders, trained_at, row_count })
  → backend/models/artifacts/delay_predictor.joblib
```

#### Anomaly Detector (`models/anomaly_detection.py`)

```
Query:
  JOIN shipments ↔ routes ↔ orders ↔ invoices
  WHERE distance > 0
  Minimum 50 rows required

Features:   [distance, cost]   (2D feature space only)

Model:
  IsolationForest(contamination=0.05, random_state=42)
  Flags the 5% most statistically deviant cost-per-distance records
  Uses path length in random trees to score outlier-ness

Persist:
  joblib.dump({ model, trained_at, row_count })
  → backend/models/artifacts/anomaly_detector.joblib
```

> Both `.joblib` artifacts are loaded at server startup — models **survive restarts without retraining**.

```
PipelineLog: "Success — CSV ingestion complete: N records from filename"
```

### Stage 6: Analytics Queries — `analytics/analytics_engine.py`

When a frontend screen loads, it hits an analytics endpoint. `AnalyticsEngine` fires SQLAlchemy ORM queries:

| Method | SQL Operation | Powers |
|---|---|---|
| `get_dashboard_kpis()` | COUNT shipments, AVG invoice.cost, COUNT routes | 4 KPI cards |
| `get_costs_by_carrier()` | GROUP BY carrier, AVG(cost) | Cost by carrier bar chart |
| `get_top_routes(10)` | GROUP BY route, COUNT(shipments), ORDER DESC | Top routes chart |
| `get_partner_performance()` | Subquery: total & delayed per carrier → join → on_time_rate | Partner performance bars |
| `get_shipment_volume_trend()` | GROUP BY strftime('%Y-%m', order_date), COUNT | Monthly volume line chart |
| `get_carrier_ranking()` | Three subqueries: total, delayed, avg_cost → join → rank | Carrier ranking table |
| `get_carrier_route_ranking(carrier)` | Same pattern filtered to one carrier | Route drill-down table |
| `generate_dynamic_insights()` | Derived from above queries | Auto-text insight cards |

### Stage 7: ML Inference Endpoints

#### Delay Risk (`POST /api/insights/predict`)

```
Input:  { carrier, origin, destination, distance, cost }
        │
        ▼
LabelEncoder.transform(carrier, origin, destination)
  Unknown values → fall back to integer 0 (safe default)
        │
        ▼
StandardScaler.transform([distance, carrier_enc,
                          origin_enc, dest_enc, cost])
        │
        ▼
LogisticRegression.predict_proba(X)[0][1]  →  probability ∈ [0.0, 1.0]
        │
        ▼
risk_level:  < 0.35 = "low"  |  0.35–0.65 = "medium"  |  ≥ 0.65 = "high"
        │
        ▼
Feature contributions (explainability):
  For each feature: contribution = coef × scaled_value
  Sort by |contribution| descending → top 3
  Tag each: "increases_risk" or "decreases_risk"
        │
        ▼
Output: { delay_probability, risk_level, top_features }
```

#### Cost Anomaly Scan (`GET /api/insights/anomalies`)

```
IsolationForest.predict(all [distance, cost] records from DB)
  → -1 = anomaly  |  +1 = normal
        │
        ▼
Filter rows where prediction == -1
        │
        ▼
For each anomalous shipment_id:
  JOIN anomaly_reviews table
  Enrich with: review_status, review_notes, reviewed_at
        │
        ▼
Output: [{ shipment_id, distance, cost,
           review_status, review_notes, reviewed_at }, ...]
```

### Stage 8: Frontend Visual Rendering

```
React component mounts (e.g. DashboardScreen)
        │
        ▼
useEffect fires → apiService.get('/analytics/dashboard')
  Axios interceptor adds: Authorization: Bearer <token>
        │
        ▼
200 OK → JSON payload arrives
        │
        ▼
setState(data) → React re-renders
        │
        ▼
KPI cards      →  plain numeric display with labels
Bar charts     →  Recharts <BarChart> + <Bar> + <XAxis> + <YAxis>
Line charts    →  Recharts <LineChart> + <Line>
Insight cards  →  styled <div> blocks (warning/success/info/error colours)
```

---

## 6. Authentication Flow

```
POST /api/auth/login  { username, password }
        │
        ▼
Backend compares against OPERATOR_USERNAME / OPERATOR_PASSWORD in .env
        │
        ▼
python-jose creates JWT:
  payload: { sub: username, exp: utcnow + ACCESS_TOKEN_EXPIRE_HOURS }
  algorithm: HS256
  secret key: AUTH_SECRET_KEY from .env
        │
        ▼
Response: { access_token, token_type: "bearer" }
        │
        ▼
Frontend stores token in sessionStorage
(clears on browser tab close — no persistent cookie)
        │
        ▼
All subsequent requests carry:
  Authorization: Bearer <token>

FastAPI dependency get_current_user() validates the JWT
on every protected route. Invalid/expired token → 401.
```

---

## 7. Tech Stack Summary

| Layer | Technology | Purpose |
|---|---|---|
| **Frontend framework** | React 18 + Vite 7 | SPA with fast HMR dev server |
| **Routing** | React Router v6 | Client-side page navigation |
| **HTTP client** | Axios | API calls with JWT interceptor |
| **Charts** | Recharts | All dashboard visualisations |
| **Backend framework** | FastAPI (Python) | REST API, async support, auto `/docs` |
| **ASGI server** | Uvicorn | Production-grade Python HTTP server |
| **ORM** | SQLAlchemy 2.0 | Database abstraction + query builder |
| **Database** | SQLite | Zero-infra file-based relational DB |
| **Data processing** | Pandas + NumPy | DataFrame pipeline operations |
| **Fuzzy matching** | RapidFuzz | Schema detection + customer name clustering |
| **ML — Delay** | scikit-learn `LogisticRegression` | Binary delay classification |
| **ML — Anomaly** | scikit-learn `IsolationForest` | Unsupervised cost outlier detection |
| **Model persistence** | joblib | Serialise/deserialise trained model artifacts |
| **Auth** | python-jose + passlib + bcrypt | JWT signing and credential verification |
| **Validation** | Pydantic v2 | Request/response schema validation |

---

## 8. Key API Endpoints Reference

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/api/auth/login` | ❌ | Get JWT token |
| `GET` | `/api/auth/me` | ✅ | Current operator info |
| `POST` | `/api/upload` | ✅ | Upload CSV, run full pipeline + ML training |
| `GET` | `/api/analytics/dashboard` | ✅ | KPIs + 4 charts + auto-insights |
| `GET` | `/api/analytics/shipments` | ✅ | Paginated, searchable, sortable shipment list |
| `GET` | `/api/analytics/carrier-ranking` | ✅ | Carrier delay rate ranking |
| `GET` | `/api/analytics/carrier/{name}/routes` | ✅ | Per-carrier route breakdown |
| `GET` | `/api/insights/` | ✅ | ML model outputs + metadata |
| `POST` | `/api/insights/predict` | ✅ | Delay risk score for hypothetical shipment |
| `GET` | `/api/insights/anomalies` | ✅ | All cost anomalies with review status |
| `PATCH` | `/api/insights/anomalies/{id}` | ✅ | Update anomaly review status |
| `GET` | `/api/logs` | ✅ | Pipeline audit log |
| `GET` | `/health` | ❌ | Server liveness check |

---

## 9. Deliberate Scope Decisions (Current Phase)

| Feature | Decision |
|---|---|
| **Single user** | One hardcoded operator. Multi-user requires a `users` table + per-user password hashing. |
| **SQLite** | Sufficient for tens of thousands of rows, zero infrastructure. PostgreSQL migration path documented in `backend/database/db.py`. |
| **CSV only** | No email/PDF/API ingestion. Carrier API connectors (Maersk, DHL) are future scope. |
| **UI polish** | Interface is functional. A full visual design rework is a planned subsequent pass. |
| **No real-time** | All data is batch-ingested. Streaming updates are future scope. |
