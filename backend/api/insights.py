from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.db import get_db
from api.upload import delay_predictor, anomaly_detector

router = APIRouter(tags=["Insights"])

@router.get("/")
async def get_insights(db: Session = Depends(get_db)):
    """
    Returns AI Insights based on current data and models.
    """
    # Demo static example of AI feature access if models aren't newly invoked
    # Normally we'd pass specific parameters, but we can query standard anomalies here.
    
    anomalies = []
    if anomaly_detector.model is not None:
        # Get historical anomalies from training phrase
        try:
            anomalies = anomaly_detector.train(db) or []
        except:
            pass
            
    # Example prediction
    sample_prediction = None
    if delay_predictor.model is not None:
        sample_prediction = {
            "sample_route": "Shanghai-LA",
            "delay_probability": round(delay_predictor.predict_delay_prob(8500, 'Maersk', 'Shanghai', 'Los Angeles', 4500), 2)
        }
        
    return {
        "delay_prediction_sample": sample_prediction,
        "recent_cost_anomalies": anomalies[:10] if anomalies else []
    }
