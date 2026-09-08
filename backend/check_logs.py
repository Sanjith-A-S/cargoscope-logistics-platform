"""Check pipeline logs for upload errors."""
from core.db import engine
from sqlalchemy import text

with engine.connect() as conn:
    rows = conn.execute(text("SELECT event_type, description FROM pipeline_logs ORDER BY id")).fetchall()
    for r in rows:
        print(f"{r[0]}: {r[1]}")
