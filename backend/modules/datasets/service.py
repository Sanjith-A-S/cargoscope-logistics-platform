"""
modules/datasets/service.py — Dataset CRUD and org-scoped query helpers.
"""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from core.models import (
    Dataset, Order, Shipment, Route, Customer,
    Invoice, AnomalyReview, PipelineLog,
)


def create_dataset(name: str, org_id: int, db: Session) -> Dataset:
    """Create a new empty dataset for the given org."""
    ds = Dataset(name=name.strip(), org_id=org_id)
    db.add(ds)
    db.commit()
    db.refresh(ds)
    return ds


def list_datasets(org_id: int, db: Session) -> List[dict]:
    """
    List all datasets belonging to the org.
    Enriches each with date_range computed from linked orders.
    """
    datasets = (
        db.query(Dataset)
        .filter(Dataset.org_id == org_id)
        .order_by(Dataset.last_updated_at.desc())
        .all()
    )

    result = []
    for ds in datasets:
        # Compute date range from orders linked to this dataset
        date_row = (
            db.query(
                func.min(Order.order_date).label("min_date"),
                func.max(Order.order_date).label("max_date"),
            )
            .filter(Order.dataset_id == ds.id)
            .first()
        )
        result.append({
            "id": ds.id,
            "name": ds.name,
            "source_row_count": ds.source_row_count or 0,
            "created_at": ds.created_at,
            "last_updated_at": ds.last_updated_at,
            "date_range_start": date_row.min_date.isoformat() if date_row and date_row.min_date else None,
            "date_range_end": date_row.max_date.isoformat() if date_row and date_row.max_date else None,
        })

    return result


def get_dataset_by_id(dataset_id: int, org_id: int, db: Session) -> Dataset:
    """Fetch a single dataset, enforcing org ownership (403 if not owned)."""
    ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    if ds.org_id != org_id:
        raise HTTPException(
            status_code=403,
            detail="Dataset does not belong to your organisation.",
        )
    return ds


def update_dataset_stats(dataset_id: int, db: Session) -> None:
    """Recompute and persist row count and last_updated_at for a dataset."""
    row_count = (
        db.query(func.count(Shipment.shipment_id))
        .filter(Shipment.dataset_id == dataset_id)
        .scalar()
        or 0
    )
    ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if ds:
        ds.source_row_count = row_count
        ds.last_updated_at = datetime.utcnow()
        db.commit()


def delete_dataset(
    dataset_id: int,
    org_id: Optional[int],  # None = admin bypass (no org check)
    db: Session,
) -> dict:
    """
    Delete a dataset and all its child records.

    Manual cascade order (SQLite doesn't enforce FK cascades by default):
      AnomalyReview → Invoice → Shipment → Order → Route → Customer → PipelineLog → Dataset

    org_id=None skips the ownership check (admin path only).
    Returns {"dataset_name": str, "deleted_rows": int} for confirmation messaging.
    """
    ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    if org_id is not None and ds.org_id != org_id:
        raise HTTPException(
            status_code=403,
            detail="Dataset does not belong to your organisation.",
        )

    dataset_name = ds.name
    shipment_count = (
        db.query(func.count(Shipment.shipment_id))
        .filter(Shipment.dataset_id == dataset_id)
        .scalar() or 0
    )

    # 1. Anomaly reviews
    db.query(AnomalyReview).filter(AnomalyReview.dataset_id == dataset_id).delete()

    # 2. Invoices — join through orders scoped to this dataset
    order_ids = (
        db.query(Order.id).filter(Order.dataset_id == dataset_id).subquery()
    )
    db.query(Invoice).filter(Invoice.order_id.in_(order_ids)).delete(synchronize_session=False)

    # 3. Shipments
    db.query(Shipment).filter(Shipment.dataset_id == dataset_id).delete()

    # 4. Orders
    db.query(Order).filter(Order.dataset_id == dataset_id).delete()

    # 5. Routes
    db.query(Route).filter(Route.dataset_id == dataset_id).delete()

    # 6. Customers
    db.query(Customer).filter(Customer.dataset_id == dataset_id).delete()

    # 7. Pipeline logs
    db.query(PipelineLog).filter(PipelineLog.dataset_id == dataset_id).delete()

    # 8. Dataset itself
    db.delete(ds)
    db.commit()

    return {"dataset_name": dataset_name, "deleted_rows": shipment_count}
