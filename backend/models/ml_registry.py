"""
ML Registry — single shared model instances for the entire application lifetime.

Both upload.py (training) and insights.py (inference) import from here so they
always operate on the same in-memory object. On startup the registry attempts to
load previously persisted artifacts from disk before falling back to untrained instances.
"""
from models.delay_prediction import DelayPredictor
from models.anomaly_detection import CostAnomalyDetector

# Attempt to restore persisted models; fall back to untrained instances
delay_predictor: DelayPredictor = DelayPredictor.load()
anomaly_detector: CostAnomalyDetector = CostAnomalyDetector.load()
