"""
modules/datasets/router.py — Dataset lifecycle endpoints.

Registration line in main.py:
    app.include_router(datasets_router, prefix="/api")
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.db import get_db
from core.auth import get_current_user
from modules.datasets.schemas import DatasetCreate
from modules.datasets import service

router = APIRouter(tags=["Datasets"])


@router.post("/datasets")
async def create_dataset(
    body: DatasetCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new empty dataset for the authenticated org."""
    ds = service.create_dataset(
        name=body.name,
        org_id=current_user["org_id"],
        db=db,
    )
    return {
        "id": ds.id,
        "name": ds.name,
        "source_row_count": 0,
        "created_at": ds.created_at,
        "last_updated_at": ds.last_updated_at,
    }


@router.get("/datasets")
async def list_datasets(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all datasets for the authenticated org."""
    datasets = service.list_datasets(org_id=current_user["org_id"], db=db)
    return {"datasets": datasets}


@router.get("/datasets/{dataset_id}")
async def get_dataset(
    dataset_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve a single dataset by ID (org-scoped)."""
    ds = service.get_dataset_by_id(
        dataset_id=dataset_id,
        org_id=current_user["org_id"],
        db=db,
    )
    return {
        "id": ds.id,
        "name": ds.name,
        "source_row_count": ds.source_row_count or 0,
        "created_at": ds.created_at,
        "last_updated_at": ds.last_updated_at,
    }


@router.delete("/datasets/{dataset_id}")
async def delete_dataset(
    dataset_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a dataset and all its shipments/orders/routes/invoices/anomaly reviews.
    Org-scoped — a user cannot delete another org's dataset.
    """
    result = service.delete_dataset(
        dataset_id=dataset_id,
        org_id=current_user["org_id"],
        db=db,
    )
    return {
        "message": f"Dataset '{result['dataset_name']}' deleted successfully.",
        "deleted_shipment_rows": result["deleted_rows"],
    }

