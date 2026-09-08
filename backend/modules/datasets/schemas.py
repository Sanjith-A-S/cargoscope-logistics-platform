"""
modules/datasets/schemas.py — Pydantic schemas for Dataset endpoints.
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DatasetCreate(BaseModel):
    name: str


class DatasetResponse(BaseModel):
    id: int
    name: str
    source_row_count: int
    created_at: datetime
    last_updated_at: datetime
    date_range_start: Optional[str] = None
    date_range_end: Optional[str] = None

    class Config:
        from_attributes = True
