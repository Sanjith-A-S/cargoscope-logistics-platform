"""
api/upload.py — CSV upload endpoint.

Changes from baseline:
  - Accepts optional dataset_id (Form field).
  - If no dataset_id: auto-creates a new Dataset for the org.
  - Validates dataset belongs to current org (403 if not).
  - Passes dataset_id + org_id to harmonize_and_store().
  - Updates Dataset.source_row_count and last_updated_at after ingestion.
  - Triggers transit model retrain (Module 5) after store.
"""
import io
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from core.db import get_db
from core.auth import get_current_user
from core.models import PipelineLog, Dataset
from pipeline.ingestion import ingest_dataset
from pipeline.cleaning import clean_data
from pipeline.harmonization import harmonize_and_store
from pipeline.schema_validation import SchemaValidationError
from modules.datasets.service import get_dataset_by_id, update_dataset_stats

router = APIRouter(tags=["Upload"])


def log_event(db: Session, event_type: str, description: str, org_id=None, dataset_id=None):
    log = PipelineLog(
        timestamp=datetime.utcnow(),
        event_type=event_type,
        description=description,
        org_id=org_id,
        dataset_id=dataset_id,
    )
    db.add(log)
    db.commit()


@router.post("/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    dataset_id: int = Form(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    org_id = current_user["org_id"]

    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    # ── Resolve or create dataset ─────────────────────────────────────────────
    if dataset_id is not None:
        # Validate ownership
        get_dataset_by_id(dataset_id=dataset_id, org_id=org_id, db=db)
    else:
        # Auto-create a new dataset named from filename + timestamp
        ds_name = f"{file.filename.rsplit('.', 1)[0]} — {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
        new_ds = Dataset(name=ds_name, org_id=org_id)
        db.add(new_ds)
        db.commit()
        db.refresh(new_ds)
        dataset_id = new_ds.id

    try:
        content = await file.read()
        log_event(db, "Upload", f"CSV file received: {file.filename} ({len(content)} bytes)",
                  org_id=org_id, dataset_id=dataset_id)

        # 1. Ingest (schema detection + mapping + validation + type coercion)
        df, mapping, coercion_warnings = ingest_dataset(
            io.BytesIO(content), dataset_name=file.filename
        )
        log_event(
            db, "Processing",
            f"Schema detected and mapped for {file.filename}: {len(df)} rows"
            + (f"; {len(coercion_warnings)} coercion warning(s)" if coercion_warnings else ""),
            org_id=org_id, dataset_id=dataset_id,
        )

        # 2. Clean
        df_clean = clean_data(df)
        log_event(db, "Processing", f"Data cleaned: {len(df_clean)} records after deduplication",
                  org_id=org_id, dataset_id=dataset_id)

        # 3. Harmonize and store (with dataset + org tagging)
        harm_result = harmonize_and_store(
            df_clean, db,
            dataset_id=dataset_id,
            org_id=org_id,
            coercion_warnings=coercion_warnings,
        )
        log_event(
            db, "Ingestion",
            f"Records harmonized and stored: {harm_result.inserted} new rows"
            f", {harm_result.skipped_duplicates} duplicates skipped",
            org_id=org_id, dataset_id=dataset_id,
        )

        # 4. Update dataset stats
        update_dataset_stats(dataset_id, db)

        # 5. Train ML models (scoped to this dataset's org)
        from models.ml_registry import delay_predictor, anomaly_detector
        delay_predictor.train(db, dataset_id=dataset_id, org_id=org_id)
        anomaly_detector.train(db, dataset_id=dataset_id, org_id=org_id)

        # 6. Train transit model (Module 5) — graceful fallback if insufficient data
        try:
            from modules.transit_model.service import retrain_transit_model
            retrain_transit_model(db=db, org_id=org_id, dataset_id=dataset_id)
        except Exception as tm_err:
            log_event(db, "Warning", f"Transit model retrain skipped: {tm_err}",
                      org_id=org_id, dataset_id=dataset_id)

        log_event(db, "Success",
                  f"CSV ingestion complete: {len(df_clean)} rows from {file.filename}",
                  org_id=org_id, dataset_id=dataset_id)

        return {
            "message": "Dataset uploaded successfully",
            "records_processed": len(df_clean),
            "records_inserted": harm_result.inserted,
            "records_skipped_duplicates": harm_result.skipped_duplicates,
            "dataset_id": dataset_id,
            "detected_schema": {k: v for k, v in mapping.items() if k != v},
            "ingestion_summary": {
                "numeric_columns": harm_result.numeric_columns_coerced,
                "categorical_columns": harm_result.categorical_columns_kept_as_string,
                "coercion_warnings": harm_result.coercion_warnings,
                "warning_count": len(harm_result.coercion_warnings),
            },
        }

    except SchemaValidationError as e:
        log_event(db, "Error",
                  f"Schema validation failed for {file.filename}: missing {e.missing_fields}",
                  org_id=org_id, dataset_id=dataset_id)
        return JSONResponse(
            status_code=400,
            content={
                "error": "Schema validation failed — the CSV is missing required columns.",
                "missing_fields": e.missing_fields,
                "hint": (
                    "Ensure your CSV contains (or has columns that map to): "
                    "shipment_id, customer, origin, destination, order_date. "
                    "Other field names like 'tracking_number' or 'buyer' are auto-mapped."
                ),
            },
        )
    except Exception as e:
        db.rollback()
        try:
            log_event(db, "Error", f"CSV upload failed for {file.filename}: {str(e)}",
                      org_id=org_id, dataset_id=dataset_id)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=str(e))

