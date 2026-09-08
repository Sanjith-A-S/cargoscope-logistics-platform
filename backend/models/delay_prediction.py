import os
import joblib
from typing import Optional
import pandas as pd
from datetime import datetime, timezone
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sqlalchemy.orm import Session
from database.models import Shipment, Order, Route, Invoice, Dataset

# Artifact directory relative to this file's location (backend/models/)
_ARTIFACT_DIR = os.path.join(os.path.dirname(__file__), "artifacts")
_ARTIFACT_PATH = os.path.join(_ARTIFACT_DIR, "delay_predictor.joblib")


class DelayPredictor:
    def __init__(self):
        self.model = None
        self.label_encoders = {}
        self._trained_at: str | None = None
        self._training_row_count: int | None = None

    # ── Persistence ────────────────────────────────────────────────────────────

    @classmethod
    def load(cls) -> "DelayPredictor":
        """Load from disk if artifact exists, else return a fresh untrained instance."""
        instance = cls()
        if os.path.exists(_ARTIFACT_PATH):
            try:
                state = joblib.load(_ARTIFACT_PATH)
                instance.model = state["model"]
                instance.label_encoders = state["label_encoders"]
                instance._trained_at = state.get("trained_at")
                instance._training_row_count = state.get("training_row_count")
                print(f"DelayPredictor loaded from disk (trained at {instance._trained_at})")
            except Exception as e:
                print(f"Failed to load DelayPredictor artifact: {e}")
        return instance

    def _save(self):
        os.makedirs(_ARTIFACT_DIR, exist_ok=True)
        state = {
            "model": self.model,
            "label_encoders": self.label_encoders,
            "trained_at": self._trained_at,
            "training_row_count": self._training_row_count,
        }
        joblib.dump(state, _ARTIFACT_PATH)
        print(f"DelayPredictor saved to {_ARTIFACT_PATH}")

    def get_metadata(self) -> dict | None:
        if self.model is None:
            return None
        return {
            "trained_at": self._trained_at,
            "training_row_count": self._training_row_count,
        }

    # ── Training ───────────────────────────────────────────────────────────────

    def train(self, db: Session, dataset_id: Optional[int] = None, org_id: Optional[int] = None):
        """Train the LogisticRegression model using historical shipment data scoped by dataset/org."""
        query = (
            db.query(
                Route.distance,
                Shipment.carrier,
                Route.origin,
                Route.destination,
                Invoice.cost,
                Shipment.is_delayed
            )
            .join(Shipment, Shipment.route_id == Route.id)
            .join(Order, Shipment.order_id == Order.id)
            .join(Invoice, Invoice.order_id == Order.id)
            .filter(Shipment.actual_delivery != None)  # Only completed shipments
        )

        if dataset_id is not None:
            query = query.filter(Shipment.dataset_id == dataset_id)
        elif org_id is not None:
            query = query.join(Dataset, Shipment.dataset_id == Dataset.id).filter(Dataset.org_id == org_id)

        results = query.all()

        if len(results) < 50:
            print(f"Not enough data to train delay predictor ({len(results)} rows, need 50)")
            return

        df = pd.DataFrame([r._asdict() for r in results])

        # Encode categorical features
        categorical_cols = ['carrier', 'origin', 'destination']
        self.label_encoders = {}
        for col in categorical_cols:
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col].astype(str))
            self.label_encoders[col] = le

        X = df[['distance', 'carrier', 'origin', 'destination', 'cost']]
        y = df['is_delayed'].astype(int)

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        self.model = Pipeline([
            ('scaler', StandardScaler()),
            ('classifier', LogisticRegression(max_iter=500))
        ])
        self.model.fit(X_train, y_train)

        self._trained_at = datetime.now(timezone.utc).isoformat()
        self._training_row_count = len(df)

        acc = self.model.score(X_test, y_test)
        print(f"DelayPredictor trained on {len(df)} rows. Accuracy: {acc:.2f}")

        self._save()

    # ── Inference ──────────────────────────────────────────────────────────────

    def _encode_input(self, carrier, origin, destination) -> dict:
        """Safely encode categorical fields using fitted label encoders."""
        encoded = {}
        for col, value in [('carrier', carrier), ('origin', origin), ('destination', destination)]:
            le = self.label_encoders.get(col)
            if le is not None and value in le.classes_:
                encoded[col] = int(le.transform([value])[0])
            else:
                encoded[col] = 0  # unknown category → fallback
        return encoded

    def predict_delay_prob(self, distance, carrier, origin, destination, cost) -> float:
        """Predict probability of delay for a single record."""
        if self.model is None:
            return 0.0
        try:
            enc = self._encode_input(carrier, origin, destination)
            X_new = pd.DataFrame([{
                'distance': distance,
                'carrier': enc['carrier'],
                'origin': enc['origin'],
                'destination': enc['destination'],
                'cost': cost,
            }])
            return float(self.model.predict_proba(X_new)[0][1])
        except Exception as e:
            print(f"Prediction error: {e}")
            return 0.0

    def get_feature_contributions(self, distance, carrier, origin, destination, cost) -> list:
        """
        Return the top 3 feature contributions for explainability.
        Uses the logistic regression coefficients × scaled feature values.
        """
        if self.model is None:
            return []
        try:
            enc = self._encode_input(carrier, origin, destination)
            raw = {
                'distance': float(distance),
                'carrier': float(enc['carrier']),
                'origin': float(enc['origin']),
                'destination': float(enc['destination']),
                'cost': float(cost),
            }
            X_new = pd.DataFrame([raw])
            scaler = self.model.named_steps['scaler']
            classifier = self.model.named_steps['classifier']
            X_scaled = scaler.transform(X_new)
            coefs = classifier.coef_[0]
            feature_names = ['distance', 'carrier', 'origin', 'destination', 'cost']
            contributions = [
                {
                    "feature": feat,
                    "value": raw[feat],
                    "contribution": float(coef * X_scaled[0][i]),
                    "direction": "increases_risk" if coef * X_scaled[0][i] > 0 else "decreases_risk",
                }
                for i, (feat, coef) in enumerate(zip(feature_names, coefs))
            ]
            # Sort by absolute contribution, return top 3
            contributions.sort(key=lambda x: abs(x["contribution"]), reverse=True)
            return contributions[:3]
        except Exception as e:
            print(f"Feature contribution error: {e}")
            return []
