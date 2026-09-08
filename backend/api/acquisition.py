import io
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database.db import get_db
from auth.auth import get_current_user

from pipeline.cleaning import clean_data
from pipeline.harmonization import harmonize_and_store
import pandas as pd

from database.models import PipelineLog
from datetime import datetime

router = APIRouter(tags=["Acquisition"], dependencies=[Depends(get_current_user)])


def log_event(db: Session, event_type: str, description: str):
    log = PipelineLog(
        timestamp=datetime.utcnow(),
        event_type=event_type,
        description=description
    )
    db.add(log)
    db.commit()


def ingest_extracted_data(extracted_records, db: Session):
    """Clean and store a list of pre-normalised record dicts."""
    if not extracted_records:
        return 0

    df = pd.DataFrame(extracted_records)

    log_event(db, "Processing", f"Cleaning {len(extracted_records)} records")
    df_clean = clean_data(df)

    log_event(db, "Ingestion", f"Harmonizing and storing {len(df_clean)} records")
    result = harmonize_and_store(df_clean, db)

    log_event(db, "Success", f"Successfully ingested {result.inserted} new records, {result.skipped_duplicates} duplicates skipped")
    return result.inserted


class IngestPayload(BaseModel):
    records: List[dict]


@router.post("/acquire/ingest")
async def ingest_preview_data(payload: IngestPayload, db: Session = Depends(get_db)):
    """Directly ingest a list of pre-normalised records (used by internal tooling)."""
    if not payload.records:
        return {"message": "No records to ingest", "records_ingested": 0}

    num_processed = ingest_extracted_data(payload.records, db)
    return {
        "message": "Data ingested successfully",
        "records_ingested": num_processed
    }


@router.get("/logs")
async def get_pipeline_logs(limit: int = 50, db: Session = Depends(get_db)):
    """Fetch recent pipeline activity logs for the Data Activity screen."""
    logs = (
        db.query(PipelineLog)
        .order_by(PipelineLog.timestamp.desc())
        .limit(limit)
        .all()
    )
    return {
        "logs": [
            {
                "timestamp": l.timestamp.isoformat(),
                "event_type": l.event_type,
                "description": l.description,
            }
            for l in logs
        ]
    }
