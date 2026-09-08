import os
import joblib
from typing import Optional
import pandas as pd
from datetime import datetime, timezone
from sklearn.ensemble import IsolationForest
from sqlalchemy.orm import Session
from database.models import Shipment, Order, Route, Invoice, Dataset

_ARTIFACT_DIR = os.path.join(os.path.dirname(__file__), "artifacts")
_ARTIFACT_PATH = os.path.join(_ARTIFACT_DIR, "anomaly_detector.joblib")


class CostAnomalyDetector:
    def __init__(self):
        self.model = None
        self._trained_at: str | None = None
        self._training_row_count: int | None = None

    # ── Persistence ────────────────────────────────────────────────────────────

    @classmethod
    def load(cls) -> "CostAnomalyDetector":
        """Load from disk if artifact exists, else return a fresh untrained instance."""
        instance = cls()
        if os.path.exists(_ARTIFACT_PATH):
            try:
                state = joblib.load(_ARTIFACT_PATH)
                instance.model = state["model"]
                instance._trained_at = state.get("trained_at")
                instance._training_row_count = state.get("training_row_count")
                print(f"CostAnomalyDetector loaded from disk (trained at {instance._trained_at})")
            except Exception as e:
                print(f"Failed to load CostAnomalyDetector artifact: {e}")
        return instance

    def _save(self):
        os.makedirs(_ARTIFACT_DIR, exist_ok=True)
        state = {
            "model": self.model,
            "trained_at": self._trained_at,
            "training_row_count": self._training_row_count,
        }
        joblib.dump(state, _ARTIFACT_PATH)
        print(f"CostAnomalyDetector saved to {_ARTIFACT_PATH}")

    def get_metadata(self) -> dict | None:
        if self.model is None:
            return None
        return {
            "trained_at": self._trained_at,
            "training_row_count": self._training_row_count,
        }

    # ── Training ───────────────────────────────────────────────────────────────

    def train(self, db: Session, dataset_id: Optional[int] = None, org_id: Optional[int] = None):
        """Fit IsolationForest on historical cost-per-distance data scoped by dataset/org. Does NOT return anomalies."""
        query = (
            db.query(Route.distance, Invoice.cost, Shipment.shipment_id)
            .join(Shipment, Shipment.route_id == Route.id)
            .join(Order, Shipment.order_id == Order.id)
            .join(Invoice, Invoice.order_id == Order.id)
            .filter(Route.distance > 0)
        )

        if dataset_id is not None:
            query = query.filter(Shipment.dataset_id == dataset_id)
        elif org_id is not None:
            query = query.join(Dataset, Shipment.dataset_id == Dataset.id).filter(Dataset.org_id == org_id)

        results = query.all()

        if len(results) < 50:
            print(f"Not enough data for IsolationForest ({len(results)} rows, need 50)")
            return

        df = pd.DataFrame([r._asdict() for r in results])
        X = df[['distance', 'cost']]

        self.model = IsolationForest(contamination=0.05, random_state=42)
        self.model.fit(X)

        self._trained_at = datetime.now(timezone.utc).isoformat()
        self._training_row_count = len(df)

        print(f"CostAnomalyDetector trained on {len(df)} rows.")
        self._save()

    # ── Inference ──────────────────────────────────────────────────────────────

    def predict(self, db: Session, dataset_id: Optional[int] = None, org_id: Optional[int] = None) -> list:
        """Run inference on the current DB data scoped by dataset/org and return anomaly records. Does NOT retrain."""
        if self.model is None:
            return []

        query = (
            db.query(Route.distance, Invoice.cost, Shipment.shipment_id)
            .join(Shipment, Shipment.route_id == Route.id)
            .join(Order, Shipment.order_id == Order.id)
            .join(Invoice, Invoice.order_id == Order.id)
            .filter(Route.distance > 0)
        )

        if dataset_id is not None:
            query = query.filter(Shipment.dataset_id == dataset_id)
        elif org_id is not None:
            query = query.join(Dataset, Shipment.dataset_id == Dataset.id).filter(Dataset.org_id == org_id)

        results = query.all()

        if not results:
            return []

        df = pd.DataFrame([r._asdict() for r in results])
        X = df[['distance', 'cost']]
        df['anomaly'] = self.model.predict(X)  # -1 = anomaly, 1 = normal
        anomalies = df[df['anomaly'] == -1]
        return anomalies[['shipment_id', 'distance', 'cost']].to_dict('records')

    def detect_anomaly(self, distance: float, cost: float) -> bool:
        """Check if a single new record is an anomaly."""
        if self.model is None:
            return False
        X_new = pd.DataFrame([{'distance': distance, 'cost': cost}])
        return self.model.predict(X_new)[0] == -1
