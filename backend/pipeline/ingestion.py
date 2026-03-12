import pandas as pd
from typing import Optional

def ingest_dataset(file_path_or_buffer) -> pd.DataFrame:
    """
    Ingest a CSV dataset into a pandas DataFrame.
    Validates required fields.
    """
    try:
        df = pd.read_csv(file_path_or_buffer)
    except Exception as e:
        raise ValueError(f"Failed to read CSV: {e}")
        
    required_columns = [
        'shipment_id', 'customer', 'origin', 'destination', 
        'carrier', 'distance', 'cost', 'order_date', 
        'expected_delivery', 'product', 'invoice_amount'
    ]
    
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in dataset: {missing_cols}")
        
    return df
