"""
modules/risk_queue/router.py — Live Risk Queue endpoint.

Registration line in main.py:
    app.include_router(risk_queue_router, prefix="/api")
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.db import get_db
from core.auth import get_current_user
from modules.risk_queue.service import score_in_transit_shipments
from modules.datasets.service import get_dataset_by_id

router = APIRouter(tags=["Risk Queue"])


@router.get("/risk-queue")
async def get_risk_queue(
    dataset_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return all in-transit shipments scored by severity for the active dataset.
    Sorted most-urgent-first. Empty list = no in-transit shipments (not an error).
    """
    # Validate org ownership
    get_dataset_by_id(dataset_id=dataset_id, org_id=current_user["org_id"], db=db)

    shipments = score_in_transit_shipments(
        db=db,
        org_id=current_user["org_id"],
        dataset_id=dataset_id,
    )

    return {
        "shipments": shipments,
        "total": len(shipments),
        "dataset_id": dataset_id,
    }
