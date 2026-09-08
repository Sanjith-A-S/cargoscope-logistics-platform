from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from database.db import get_db
from database.models import Customer, Order, Shipment, Invoice, Route, AnomalyReview, Dataset
from auth.auth import get_current_user

router = APIRouter(tags=["Insights"], dependencies=[Depends(get_current_user)])


# ─── Pydantic schemas ─────────────────────────────────────────────────────────

class PredictRequest(BaseModel):
    carrier: str
    origin: str
    destination: str
    distance: float
    cost: float


class AnomalyStatusUpdate(BaseModel):
    status: str  # open | investigated | dismissed
    notes: Optional[str] = ""


# ─── Lazy import of registry (avoids circular imports at startup) ──────────────

def _get_registry():
    from models.ml_registry import delay_predictor, anomaly_detector
    return delay_predictor, anomaly_detector


def _resolve_scoped_dataset(dataset_id: Optional[int], org_id: int, db: Session) -> Optional[int]:
    if dataset_id is not None:
        ds = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.org_id == org_id).first()
        if not ds:
            raise HTTPException(status_code=403, detail="Dataset does not belong to your organisation.")
        return dataset_id
    ds = db.query(Dataset).filter(Dataset.org_id == org_id).order_by(Dataset.last_updated_at.desc()).first()
    return ds.id if ds else None


# ─── GET /api/insights/ ───────────────────────────────────────────────────────

@router.get("/")
async def get_insights(
    dataset_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Returns ML insights: delay prediction sample, cost anomalies, and model metadata."""
    delay_predictor, anomaly_detector = _get_registry()
    result = {}
    org_id = current_user.get("org_id")
    target_dataset_id = _resolve_scoped_dataset(dataset_id, org_id, db) if org_id else dataset_id

    # Delay prediction sample
    try:
        if delay_predictor.model is None:
            delay_predictor.train(db, dataset_id=target_dataset_id, org_id=org_id)

        if delay_predictor.model is not None:
            sample_query = (
                db.query(Route.origin, Route.destination, Route.distance, Shipment.carrier)
                .join(Shipment, Shipment.route_id == Route.id)
            )
            if target_dataset_id is not None:
                sample_query = sample_query.filter(Shipment.dataset_id == target_dataset_id)
            elif org_id is not None:
                sample_query = sample_query.join(Dataset, Shipment.dataset_id == Dataset.id).filter(Dataset.org_id == org_id)

            sample = sample_query.first()
            if sample:
                cost_query = db.query(func.avg(Invoice.cost))
                if target_dataset_id is not None:
                    cost_query = cost_query.filter(Invoice.dataset_id == target_dataset_id)
                avg_cost = cost_query.scalar() or 0

                prob = delay_predictor.predict_delay_prob(
                    sample.distance or 0, sample.carrier or 'Unknown',
                    sample.origin or 'Unknown', sample.destination or 'Unknown', avg_cost
                )
                result["delay_prediction_sample"] = {
                    "sample_route": f"{sample.origin} → {sample.destination} via {sample.carrier}",
                    "delay_probability": prob,
                }

        result["delay_model_metadata"] = delay_predictor.get_metadata()
    except Exception as e:
        print(f"Delay prediction error: {e}")
        result["delay_model_metadata"] = None

    # Cost anomalies — predict only, do NOT retrain
    try:
        if anomaly_detector.model is None:
            anomaly_detector.train(db, dataset_id=target_dataset_id, org_id=org_id)

        if anomaly_detector.model is not None:
            anomalies = anomaly_detector.predict(db, dataset_id=target_dataset_id, org_id=org_id)
            result["recent_cost_anomalies"] = anomalies[:10] if anomalies else []
        else:
            result["recent_cost_anomalies"] = []

        result["anomaly_model_metadata"] = anomaly_detector.get_metadata()
    except Exception as e:
        print(f"Anomaly detection error: {e}")
        result["recent_cost_anomalies"] = []
        result["anomaly_model_metadata"] = None

    return result


# ─── POST /api/insights/predict ───────────────────────────────────────────────

@router.post("/predict")
async def predict_delay(payload: PredictRequest, db: Session = Depends(get_db)):
    """Return delay risk probability and top feature contributions for a hypothetical shipment."""
    delay_predictor, _ = _get_registry()

    if delay_predictor.model is None:
        raise HTTPException(
            status_code=400,
            detail="Delay predictor has not been trained yet. Upload a CSV dataset first."
        )

    prob = delay_predictor.predict_delay_prob(
        payload.distance, payload.carrier, payload.origin, payload.destination, payload.cost
    )

    contributions = delay_predictor.get_feature_contributions(
        payload.distance, payload.carrier, payload.origin, payload.destination, payload.cost
    )

    if prob >= 0.65:
        risk_level = "high"
    elif prob >= 0.35:
        risk_level = "medium"
    else:
        risk_level = "low"

    return {
        "delay_probability": prob,
        "risk_level": risk_level,
        "top_features": contributions,
        "model_trained": True,
    }


# ─── GET /api/insights/anomalies ─────────────────────────────────────────────

@router.get("/anomalies")
async def get_anomalies(
    dataset_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Return detected cost anomalies with their current review status."""
    _, anomaly_detector = _get_registry()

    if anomaly_detector.model is None:
        return {"anomalies": [], "model_trained": False}

    org_id = current_user.get("org_id")
    target_dataset_id = _resolve_scoped_dataset(dataset_id, org_id, db) if org_id else dataset_id
    raw_anomalies = anomaly_detector.predict(db, dataset_id=target_dataset_id, org_id=org_id)

    # Enrich with review status from the anomaly_reviews table
    enriched = []
    for a in raw_anomalies:
        sid = a.get("shipment_id", "")
        review = db.query(AnomalyReview).filter(AnomalyReview.shipment_id == sid).first()
        enriched.append({
            **a,
            "review_status": review.status if review else "open",
            "review_notes": review.notes if review else "",
            "reviewed_at": review.reviewed_at.isoformat() if review and review.reviewed_at else None,
        })

    return {"anomalies": enriched, "model_trained": True}


# ─── PATCH /api/insights/anomalies/{shipment_id} ─────────────────────────────

@router.patch("/anomalies/{shipment_id}")
async def update_anomaly_status(
    shipment_id: str,
    payload: AnomalyStatusUpdate,
    db: Session = Depends(get_db)
):
    """Update review status for an anomaly."""
    valid_statuses = {"open", "investigated", "dismissed"}
    if payload.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{payload.status}'. Must be one of: {valid_statuses}"
        )

    review = db.query(AnomalyReview).filter(AnomalyReview.shipment_id == shipment_id).first()
    if review:
        review.status = payload.status
        review.notes = payload.notes or ""
        review.reviewed_at = datetime.utcnow()
    else:
        review = AnomalyReview(
            shipment_id=shipment_id,
            status=payload.status,
            notes=payload.notes or "",
            reviewed_at=datetime.utcnow(),
        )
        db.add(review)

    db.commit()
    return {"message": "Anomaly status updated", "shipment_id": shipment_id, "status": payload.status}
