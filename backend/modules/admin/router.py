"""
modules/admin/router.py — Admin-only API endpoints.

All routes require get_admin_user() — any non-admin JWT gets 403.

Registration line in main.py:
    app.include_router(admin_router, prefix="/api")
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.db import get_db
from core.auth import get_admin_user
from modules.admin import service

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/users")
async def list_users(
    _admin: dict = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """List all registered users with org info and data stats."""
    return {"users": service.list_all_users(db)}


@router.get("/users/{user_id}/datasets")
async def get_user_datasets(
    user_id: int,
    _admin: dict = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """List all datasets belonging to a user's org."""
    return {"datasets": service.get_user_datasets(user_id, db)}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    _admin: dict = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """
    Delete a user, their org, and all associated data.
    Irreversible — requires explicit confirmation in the frontend before calling.
    """
    result = service.admin_delete_user(user_id, db)
    return {
        "message": (
            f"User '{result['deleted_email']}' (org: '{result['deleted_org']}') deleted. "
            f"{result['deleted_datasets']} datasets and "
            f"{result['deleted_shipment_rows']} shipment rows removed."
        ),
        **result,
    }


@router.delete("/datasets/{dataset_id}")
async def delete_dataset(
    dataset_id: int,
    _admin: dict = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Delete any dataset regardless of which org owns it (admin bypass)."""
    result = service.admin_delete_dataset(dataset_id, db)
    return {
        "message": f"Dataset '{result['dataset_name']}' deleted successfully.",
        "deleted_shipment_rows": result["deleted_rows"],
    }
