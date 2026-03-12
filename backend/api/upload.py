import io
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from database.db import get_db
from pipeline.ingestion import ingest_dataset
from pipeline.cleaning import clean_data
from pipeline.harmonization import harmonize_and_store
from models.delay_prediction import DelayPredictor
from models.anomaly_detection import CostAnomalyDetector

router = APIRouter(tags=["Upload"])

# We instantiate globally to keep trained models in memory (rough prototype)
delay_predictor = DelayPredictor()
anomaly_detector = CostAnomalyDetector()

@router.post("/upload")
async def upload_dataset(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
        
    try:
        content = await file.read()
        
        # 1. Ingest
        df = ingest_dataset(io.BytesIO(content))
        
        # 2. Clean
        df_clean = clean_data(df)
        
        # 3. Harmonize and store
        harmonize_and_store(df_clean, db)
        
        # 4. Train AI models on new data so they provide insights later
        delay_predictor.train(db)
        anomaly_detector.train(db)
        
        return {
            "message": "Dataset successfully uploaded, cleaned, and ingested.",
            "records_processed": len(df_clean)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
