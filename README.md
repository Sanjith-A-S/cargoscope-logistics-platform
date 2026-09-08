# CargoScope

**An exception-management platform for logistics ops managers, not another analytics dashboard.**

CargoScope is purpose-built for operations and logistics managers at small-to-mid-size shippers who move freight through third-party carriers (e.g., Safexpress, Blue Dart, Delhivery, TCI Express, DTDC, regional LTL). It replaces messy spreadsheet-based shipment trackers and backward-looking BI dashboards with proactive operational visibility. Instead of merely summarizing deliveries that were already late last month, CargoScope surfaces which in-transit shipments are at risk of missing their delivery SLA **right now**, why they are flagged, and what immediate action is required.

---

## The Problem This Solves

Logistics operations for small-to-mid-size shippers face three systemic gaps:

1. **Spreadsheets Remain the Operational Default:** Over 70% of mid-market shippers manage day-to-day freight across dozens of carrier portals, daily email manifests, and fragmented spreadsheets. This is not an outdated legacy habit—it is the functional norm because enterprise Transportation Management Systems (TMS) are prohibitively complex, costly, and rigid for mid-sized freight volumes.
2. **Dashboards Report History; Ops Needs Intervention:** Most analytics platforms produce historical post-mortems (e.g., *"Carrier X achieved 82% on-time delivery last quarter"*). By the time an ops manager sees this metric, client relationships have already soured and penalty clauses have been triggered. Ops teams require real-time visibility into active consignments currently in transit that are statistically veering toward a delay before the customer calls.
3. **Flat SLAs and Naive Delay Metrics Miss Reality:** Traditional tracking relies on a binary date comparison (`actual > expected`) against a single carrier-provided SLA. In reality:
   - **Weight and payload class radically alter transit times:** A carrier that delivers 15 kg parcels in 48 hours often takes 5 days for a 600 kg pallet on the same lane.
   - **On-Time is meaningless without In-Full (OTIF):** A shipment that arrives strictly on the promised date but is missing 20% of the ordered quantity is a failed delivery. Naive date tracking marks this as a success.

---

## Core Features

CargoScope bridges these gaps with a structured exception-management workflow:

- **Live Risk Queue:** Evaluates every in-transit shipment against historical route-and-weight benchmarks. Flags high-risk consignments with clear, plain-language operational reasons (e.g., *"Transit duration exceeds carrier p90 benchmark for heavy cargo on Indore → Nagpur lane"*), enabling proactive intervention.
- **Weight-Adjusted Transit Modeling:** Computes realistic expected delivery windows based on granular historical `carrier × distance_bucket × weight_class` patterns. Employs a confidence-graded fallback hierarchy (carrier-lane-weight → carrier-lane → carrier-weight → lane average) so estimates remain robust even on low-volume lanes.
- **Real OTIF (On-Time, In-Full) Tracking:** Measures true fulfillment health by simultaneously evaluating delivery timeliness against contractual SLAs and quantity completion (`shipped_qty == order_qty`), isolating partial fulfillment failures from transit delays.
- **Granular Carrier Scorecards:** Delivers longitudinal performance trends coupled with weight-band breakdowns. Instantly reveals critical operational patterns—such as a carrier performing reliably on parcels under 100 kg but severely degrading above 300 kg.
- **Cost Intelligence & Accessorial Audit:** Audits invoiced freight costs against contracted baseline rates and identifies accessorial surcharges (e.g., detention fees, liftgate charges, residential delivery penalties), moving beyond basic statistical outlier detection.
- **Multi-Dataset Lifecycle Management:** Supports creating independent dataset workspaces or appending/updating existing datasets with automated record deduplication, schema versioning, and dataset-scoped metric isolation.
- **Multi-Tenant Architecture:** Provides strict organizational data boundaries with secure per-user JWT authentication and organization-scoped database queries.
- **Admin Portal:** Dedicated management console for platform administrators to monitor tenant organizations, user accounts, and dataset ingestion metrics.
- **Resilient Fuzzy CSV Ingestion:** Features an adaptive schema-mapping engine that normalizes irregular headers (e.g., `consignment_no`, `from_port`, `freight_price`) against declared data types (numeric, date, categorical) with automatic unit standardization (such as converting `lb` to `kg`).
- **Optional LLM Narration Layer:** Provides plain-language narrative summaries of structured analytical findings for executive briefings, strictly isolated from the deterministic underlying math.

---

## System Architecture

CargoScope is built with a decoupled, modular architecture where each operational domain is encapsulated into an isolated service module with dedicated schemas, routes, and business logic.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           CargoScope Frontend                           │
│     React 19 + Vite + TailwindCSS + Lucide Icons + Recharts Analytics   │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ (REST API / JWT Bearer Auth)
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       FastAPI Application Core                          │
│                                                                         │
│  ┌───────────────────────┐  ┌───────────────────┐  ┌─────────────────┐  │
│  │   Auth & Multi-Tenant │  │ Ingestion Engine  │  │  Admin Portal   │  │
│  │   JWT / Org Scoping   │  │ Fuzzy Schema Map  │  │  User / Tenant  │  │
│  └───────────┬───────────┘  └─────────┬─────────┘  └────────┬────────┘  │
│              │                        │                     │           │
│  ┌───────────▼────────────────────────▼─────────────────────▼────────┐  │
│  │                     Feature Domain Modules                        │  │
│  │  • risk_queue       • transit_model       • otif                  │  │
│  │  • cost_intel       • carrier_scorecards  • anomaly_detection     │  │
│  │  • datasets_mgr     • narration (optional LLM)                    │  │
│  └────────────────────────────────────┬──────────────────────────────┘  │
└───────────────────────────────────────┼─────────────────────────────────┘
                                        │
                    ┌───────────────────┴───────────────────┐
                    ▼                                       ▼
    ┌───────────────────────────────┐       ┌───────────────────────────────┐
    │     SQLAlchemy ORM + SQLite   │       │   Scikit-Learn ML Engines     │
    │  Tenant & Dataset Scoped Data │       │   • Isolation Forest (Cost)   │
    │  Shipments / Reviews / Audits │       │   • Logistic Regression (Delay)│
    └───────────────────────────────┘       └───────────────────────────────┘
```

### Ingestion Pipeline Flow

```
[Raw CSV Export] 
       │
       ▼
[1. Fuzzy Schema Detection]  ──► Matches irregular column headers to canonical names
       │
       ▼
[2. Type Coercion & Cleaning] ──► Normalizes dates (ISO), parses numeric rates, converts units (lb->kg)
       │
       ▼
[3. Schema Validation]       ──► Rejects corrupted rows, validates required constraints
       │
       ▼
[4. Dataset Storage]         ──► Stores in SQLite scoped to active Organization & Dataset ID
       │
       ▼
[5. Analytics & ML Engines]  ──► Re-computes OTIF, updates transit model weights, trains risk models
```

> **Scope Boundary Note:** CargoScope models historical and active carrier outcome data for shippers outsourcing freight to third-party carriers. It intentionally **does not** handle real-time GPS telemetry, in-cab telematics, turn-by-turn routing, or fleet dispatch optimization—those belong to a carrier fleet management system (FMS), not a shipper-side exception platform.

---

## Getting Started

### Prerequisites
- **Python:** Version 3.10 or higher
- **Node.js:** Version 18.0 or higher (with `npm`)
- **Git**

---

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create and activate a virtual environment
python -m venv venv
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On Linux / macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
```

Edit `backend/.env` with your desired configuration:

```ini
# Secret key for JWT signing
AUTH_SECRET_KEY=generate-a-secure-random-secret-key-here
ACCESS_TOKEN_EXPIRE_HOURS=24

# Admin portal credentials
ADMIN_USERNAME=admin
# Generate bcrypt hash: python -c "from passlib.context import CryptContext; print(CryptContext(schemes=['bcrypt']).hash('yourpassword'))"
ADMIN_PASSWORD_HASH=$2b$12$e8YqJ2...
```

Run the backend server:

```bash
uvicorn main:app --reload --port 8000
```
- API Base: `http://localhost:8000`
- Interactive OpenAPI Docs: `http://localhost:8000/docs`

---

### 2. Frontend Setup

```bash
# Navigate to frontend directory (in a new terminal)
cd frontend

# Install Node dependencies
npm install

# Start Vite development server
npm run dev
```
- Web Application: `http://localhost:5173`

---

### 3. First-Time Walkthrough

1. **Sign Up / Login:** Open `http://localhost:5173/login`, create a new user account with your organization name, and log in.
2. **Upload Dataset:** Navigate to **Settings** (`/settings`) → click **Upload CSV**.
3. **Select Sample Data:** Choose `datasets/indian_logistics_primary.csv` to instantly populate ~1,000 shipment records, train the machine learning models, and derive carrier scorecards.
4. **Monitor Exceptions:** Visit the **Risk Queue** to review at-risk in-transit shipments, check the **Carrier Performance** tab for weight-band breakdowns, and inspect flagged outliers in **Anomaly Review**.

---

## Sample Data

CargoScope includes synthetic Indian freight datasets in the [`datasets/`](file:///d:/Dev%20Mode/FragTradeAnalysis/Fragmented-Trade-Data-Analysis/datasets) directory:

- **`indian_logistics_primary.csv`** (~1,000 rows): Primary baseline shipment dataset across major Indian transport corridors with 7 major carriers, detailed item weights, order vs. shipped quantities, contracted rates, and accessorial fees.
- **`indian_logistics_update.csv`** (~180 rows): Incremental delivery update file to test the append, merge, and record deduplication workflow.
- **`indian_logistics_new_dataset.csv`** (~400 rows): Separate freight slice to verify multi-dataset workspace isolation and dynamic dataset switching.
- **`indian_logistics_corrupt.csv`** (~500 rows): Ingestion stress-test file containing irregular column names, messy date formats, and mixed weight units.

For complete schema details and column documentation, see [`datasets/DATASET_README.md`](file:///d:/Dev%20Mode/FragTradeAnalysis/Fragmented-Trade-Data-Analysis/datasets/DATASET_README.md).

---

## Project Scope & Honest Limitations

To maintain architectural focus and credibility, CargoScope explicitly identifies its current boundary constraints:

- **No Direct Carrier EDI / Real-Time API Integrations:** Ingestion is file- and batch-driven (CSV/Excel exports). Small-to-mid-size shippers operate on daily manifests and scheduled portal exports rather than direct carrier EDI 214 integrations.
- **No Vehicle Dispatch or Fleet Routing:** CargoScope is built for the *shipper*, not the carrier. It does not optimize turn-by-turn routes or dispatch owned trucks.
- **Single User per Organization in Current Release:** User isolation is fully tenant-scoped by organization ID, but multi-user team invite workflows within the same organization are slated for a future iteration.
- **SQLite Database Backend:** SQLite provides zero-configuration local deployment for evaluation and development. Production high-throughput deployments will require migrating the SQLAlchemy connection string to PostgreSQL.

---

## Who This Is For

CargoScope is tailored for **Logistics Managers, Supply Chain Directors, and Freight Operations Leads** at small-to-mid-size companies moving physical goods across industries such as:

- **Auto Components & Industrial Equipment** (managing critical assembly-line delivery deadlines)
- **FMCG & Packaged Foods** (enforcing OTIF compliance to prevent retailer chargebacks)
- **Textiles, Apparel & D2C Brands** (monitoring regional express courier SLAs)
- **Pharmaceutical & Chemical Distribution** (tracking high-value consignments and accessorial costs)

If you currently track active freight using shared spreadsheets and manually check carrier portals to find out why a delivery is late, CargoScope is built for you.

---

## Contributing & Development

Contributions and architectural feedback are welcome.

1. Fork the repository and create a feature branch (`git checkout -b feature/new-analytics-module`).
2. Verify all backend tests and lint checks:
   ```bash
   cd backend && pytest
   cd frontend && npm run lint
   ```
3. Commit your changes with clear, descriptive commit messages.
4. Open a Pull Request detailing the problem solved and verification steps.

---

## License

This project is licensed under the terms specified by the repository maintainers. *(See `LICENSE` file or contact maintainers for commercial licensing terms).*

---

## Contact

For inquiries, support, or questions regarding CargoScope:
- **Repository:** [Fragmented-Trade-Data-Analysis](https://github.com/Sanjith-A-S/Fragmented-Trade-Data-Analysis)
- **Issue Tracker:** [GitHub Issues](https://github.com/Sanjith-A-S/Fragmented-Trade-Data-Analysis/issues)
