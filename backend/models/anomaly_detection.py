import pandas as pd
from sklearn.ensemble import IsolationForest
from sqlalchemy.orm import Session
from database.models import Shipment, Order, Route, Invoice

class CostAnomalyDetector:
    def __init__(self):
        self.model = None

    def train(self, db: Session):
        """
        Train IsolationForest on historical cost per distance data
        """
        results = (
            db.query(
                Route.distance,
                Invoice.cost,
                Shipment.shipment_id
            )
            .join(Shipment, Shipment.route_id == Route.id)
            .join(Order, Shipment.order_id == Order.id)
            .join(Invoice, Invoice.order_id == Order.id)
            .filter(Route.distance > 0)
            .all()
        )
        
        if len(results) < 50:
            print("Not enough data for IsolationForest")
            return
            
        df = pd.DataFrame([r._asdict() for r in results])
        
        # We look at cost vs distance
        X = df[['distance', 'cost']]
        
        self.model = IsolationForest(contamination=0.05, random_state=42)
        self.model.fit(X)
        print("Cost Anomaly Detector Trained.")
        
        # Predict on training data to flag existing anomalies
        df['anomaly'] = self.model.predict(X) # -1 is anomaly, 1 is normal
        anomalies = df[df['anomaly'] == -1]
        
        return anomalies.to_dict('records')

    def detect_anomaly(self, distance, cost):
        """
        Check if a single new record is an anomaly
        """
        if self.model is None:
            return False
            
        X_new = pd.DataFrame([{'distance': distance, 'cost': cost}])
        pred = self.model.predict(X_new)[0]
        return pred == -1 # True if anomaly
