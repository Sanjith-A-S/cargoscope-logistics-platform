"""
modules/admin/schemas.py — Pydantic response schemas for admin endpoints.
"""
from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class AdminUserItem(BaseModel):
    user_id: int
    email: str
    org_id: int
    org_name: str
    signup_date: datetime
    dataset_count: int
    total_shipment_rows: int

    class Config:
        from_attributes = True


class AdminDatasetItem(BaseModel):
    dataset_id: int
    name: str
    org_id: int
    source_row_count: int
    created_at: datetime
    last_updated_at: datetime
    date_range_start: Optional[str] = None
    date_range_end: Optional[str] = None

    class Config:
        from_attributes = True
