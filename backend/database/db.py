"""
database/db.py — backward-compatibility shim.
The canonical implementation is now in core/db.py.
All existing imports (pipeline/, analytics/, api/) continue to work unchanged.
"""
from core.db import Base, engine, SessionLocal, get_db  # noqa: F401
