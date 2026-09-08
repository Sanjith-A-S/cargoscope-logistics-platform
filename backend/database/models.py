"""
database/models.py — backward-compatibility shim.
The canonical implementation is now in core/models.py.
"""
from core.models import (  # noqa: F401
    Base,
    Organization,
    User,
    Dataset,
    PipelineLog,
    Customer,
    Route,
    Order,
    Shipment,
    Invoice,
    AnomalyReview,
)
