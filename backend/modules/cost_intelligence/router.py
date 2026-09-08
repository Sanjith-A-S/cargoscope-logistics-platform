"""
modules/cost_intelligence/router.py — Lanes and enhanced anomaly endpoints.

Registration line in main.py:
    app.include_router(cost_intel_router, prefix="/api/analytics")
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.db import get_db
from core.auth import get_current_user
from modules.datasets.service import get_dataset_by_id
from modules.cost_intelligence.service import get_lane_summary, get_cost_anomalies

router = APIRouter(tags=["Cost Intelligence"])


@router.get("/lanes")
async def get_lanes(
    dataset_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return OTIF + avg cost aggregated by (origin, destination) lane, worst first."""
    get_dataset_by_id(dataset_id=dataset_id, org_id=current_user["org_id"], db=db)
    lanes = get_lane_summary(db=db, org_id=current_user["org_id"], dataset_id=dataset_id)
    return {"lanes": lanes, "total": len(lanes)}


@router.get("/anomalies-v2")
async def get_cost_anomalies_v2(
    dataset_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return enhanced cost anomalies with detection method labeling."""
    get_dataset_by_id(dataset_id=dataset_id, org_id=current_user["org_id"], db=db)
    anomalies = get_cost_anomalies(db=db, org_id=current_user["org_id"], dataset_id=dataset_id)
    return {"anomalies": anomalies, "total": len(anomalies)}
