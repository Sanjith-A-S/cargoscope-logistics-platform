"""
modules/admin/service.py — Query logic for admin-only operations.

All functions here bypass org scoping (admin can see all orgs).
"""
from typing import List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi import HTTPException

from core.models import (
    User, Organization, Dataset, Shipment, Order,
    Route, Customer, Invoice, AnomalyReview, PipelineLog,
)
from modules.datasets.service import delete_dataset as _delete_dataset_scoped


def list_all_users(db: Session) -> List[dict]:
    """
    Return all users across all orgs, enriched with:
      - org name, signup date, dataset count, total shipment rows.
    """
    users = db.query(User).order_by(User.created_at.desc()).all()
    result = []
    for user in users:
        org = db.query(Organization).filter(Organization.id == user.org_id).first()
        dataset_count = (
            db.query(func.count(Dataset.id))
            .filter(Dataset.org_id == user.org_id)
            .scalar() or 0
        )
        total_rows = (
            db.query(func.count(Shipment.shipment_id))
            .join(Dataset, Dataset.id == Shipment.dataset_id)
            .filter(Dataset.org_id == user.org_id)
            .scalar() or 0
        )
        result.append({
            "user_id": user.id,
            "email": user.email,
            "org_id": user.org_id,
            "org_name": org.name if org else "(no org)",
            "signup_date": user.created_at,
            "dataset_count": dataset_count,
            "total_shipment_rows": total_rows,
        })
    return result


def get_user_datasets(user_id: int, db: Session) -> List[dict]:
    """Return all datasets belonging to the org of a given user."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    datasets = (
        db.query(Dataset)
        .filter(Dataset.org_id == user.org_id)
        .order_by(Dataset.last_updated_at.desc())
        .all()
    )
    result = []
    for ds in datasets:
        date_row = (
            db.query(
                func.min(Order.order_date).label("min_date"),
                func.max(Order.order_date).label("max_date"),
            )
            .filter(Order.dataset_id == ds.id)
            .first()
        )
        result.append({
            "dataset_id": ds.id,
            "name": ds.name,
            "org_id": ds.org_id,
            "source_row_count": ds.source_row_count or 0,
            "created_at": ds.created_at,
            "last_updated_at": ds.last_updated_at,
            "date_range_start": date_row.min_date.isoformat() if date_row and date_row.min_date else None,
            "date_range_end": date_row.max_date.isoformat() if date_row and date_row.max_date else None,
        })
    return result


def admin_delete_dataset(dataset_id: int, db: Session) -> dict:
    """
    Delete a dataset (admin path — no org ownership check).
    Reuses the cascading delete logic from datasets/service.py.
    """
    return _delete_dataset_scoped(dataset_id=dataset_id, org_id=None, db=db)


def admin_delete_user(user_id: int, db: Session) -> dict:
    """
    Delete a user, their org, and everything owned by that org:
      All datasets → all their shipments/orders/routes/invoices/anomaly_reviews/logs.

    Since each org currently has exactly one user, deleting the user
    means deleting the whole org's data.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    org_id = user.org_id
    org = db.query(Organization).filter(Organization.id == org_id).first()
    org_name = org.name if org else "(unknown)"

    # Get all datasets for this org, then cascade-delete each
    datasets = db.query(Dataset).filter(Dataset.org_id == org_id).all()
    dataset_count = len(datasets)
    total_rows = 0

    for ds in datasets:
        result = _delete_dataset_scoped(dataset_id=ds.id, org_id=None, db=db)
        total_rows += result.get("deleted_rows", 0)

    # Delete the user
    db.delete(user)
    db.flush()

    # Delete the org (may have other pipeline logs not tied to a dataset)
    db.query(PipelineLog).filter(PipelineLog.org_id == org_id).delete()
    if org:
        db.delete(org)

    db.commit()

    return {
        "deleted_email": user.email,
        "deleted_org": org_name,
        "deleted_datasets": dataset_count,
        "deleted_shipment_rows": total_rows,
    }
