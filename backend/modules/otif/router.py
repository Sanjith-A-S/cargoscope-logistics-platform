"""
modules/otif/router.py — OTIF analytics endpoint.

Registration line in main.py:
    app.include_router(otif_router, prefix="/api/analytics")
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.db import get_db
from core.auth import get_current_user
from modules.otif.service import compute_otif

router = APIRouter(tags=["OTIF"])


@router.get("/otif")
async def get_otif(
    dataset_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Compute and return OTIF metrics for the specified dataset (org-scoped)."""
    result = compute_otif(
        db=db,
        org_id=current_user["org_id"],
        dataset_id=dataset_id,
    )
    if result["total_shipments"] == 0:
        raise HTTPException(
            status_code=409,
            detail={"code": "NO_DATASET", "message": "No delivered shipments found for this dataset."},
        )
    return result
