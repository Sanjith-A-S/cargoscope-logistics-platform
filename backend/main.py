from dotenv import load_dotenv
load_dotenv()

"""
main.py — FastAPI application entry point.

To add a module: add one include_router() line below.
To remove a module: remove that line. Nothing else needs to change.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ─── Core database + models ───────────────────────────────────────────────────
from core.db import engine, Base
import core.models  # registers all ORM models (incl. Organization, User, Dataset)

# ─── Legacy API routers (baseline, kept for backward compat) ──────────────────
from api import upload, analytics, insights, acquisition

# ─── Module routers ───────────────────────────────────────────────────────────
from modules.auth.router import router as auth_router
from modules.datasets.router import router as datasets_router
from modules.otif.router import router as otif_router
from modules.risk_queue.router import router as risk_queue_router
from modules.cost_intelligence.router import router as cost_intel_router
from modules.narration.router import router as narration_router
from modules.admin.router import router as admin_router

# ─── Database initialisation ──────────────────────────────────────────────────
# Create tables if they do not exist (preserve existing data)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Trade Intelligence Platform API")

# ─── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ──────────────────────────────────────────────────────────────────
# Module routers — one line per module. Adding/removing a module = one line here.
app.include_router(auth_router, prefix="/api")
app.include_router(datasets_router, prefix="/api")
app.include_router(otif_router, prefix="/api/analytics")
app.include_router(risk_queue_router, prefix="/api")
app.include_router(cost_intel_router, prefix="/api/analytics")
app.include_router(narration_router, prefix="/api")
app.include_router(admin_router, prefix="/api")

# Legacy routers (baseline — preserved, now dataset-scoped internally)
app.include_router(upload.router, prefix="/api")
app.include_router(analytics.router, prefix="/api/analytics")
app.include_router(insights.router, prefix="/api/insights")
app.include_router(acquisition.router, prefix="/api")


# ─── Health checks ────────────────────────────────────────────────────────────
@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/health/db")
def health_db():
    from core.db import engine, DB_PATH
    from sqlalchemy import text, inspect
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        return {
            "status": "ok",
            "database": "connected",
            "db_path": DB_PATH,
            "tables": tables,
            "table_count": len(tables),
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "detail": str(e)},
        )


@app.get("/")
def read_root():
    return {"message": "Trade Intelligence Platform API — see /docs"}

