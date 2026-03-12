import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sqlalchemy.orm import Session
from database.models import Shipment, Order, Route, Invoice

class DelayPredictor:
    def __init__(self):
        self.model = None
        self.label_encoders = {}
        
    def train(self, db: Session):
        """
        Train the LogisticRegression model using existing historical shipment data.
        """
        # Fetch data
        results = (
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
            .filter(Shipment.actual_delivery != None) # Only completed shipments
            .all()
        )
        
        if len(results) < 50:
            print("Not enough data to train delay predictor")
            return
            
        df = pd.DataFrame([r._asdict() for r in results])
        
        # Encoding categorical features
        categorical_cols = ['carrier', 'origin', 'destination']
        for col in categorical_cols:
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col].astype(str))
            self.label_encoders[col] = le
            
        X = df[['distance', 'carrier', 'origin', 'destination', 'cost']]
        y = df['is_delayed'].astype(int)
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        self.model = Pipeline([
            ('scaler', StandardScaler()),
            ('classifier', LogisticRegression())
        ])
        
        self.model.fit(X_train, y_train)
        print(f"Delay Classifier Trained. Accuracy: {self.model.score(X_test, y_test):.2f}")

    def predict_delay_prob(self, distance, carrier, origin, destination, cost):
        """
        Predict probability of delay for a single new record.
        """
        if self.model is None:
            return 0.0
            
        data = {
            'distance': distance,
            'carrier': carrier,
            'origin': origin,
            'destination': destination,
            'cost': cost
        }
        
        # Encode features safely
        try:
            for col, le in self.label_encoders.items():
                if data[col] in le.classes_:
                    data[col] = le.transform([data[col]])[0]
                else:
                    data[col] = 0 # unknown category fallback
                    
            X_new = pd.DataFrame([data])
            prob = self.model.predict_proba(X_new)[0][1] # Probability of class 1 (delayed)
            return float(prob)
        except Exception as e:
            print(f"Prediction error: {e}")
            return 0.0
