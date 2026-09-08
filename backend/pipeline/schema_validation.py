import pandas as pd

REQUIRED_FIELDS = [
    "shipment_id",
    "customer",
    "origin",
    "destination",
    "order_date"
]

class SchemaValidationError(ValueError):
    def __init__(self, missing_fields):
        self.missing_fields = missing_fields
        super().__init__("Missing required fields")

def validate_schema(df: pd.DataFrame):
    """
    Ensure required platform fields exist after mapping.
    Raises SchemaValidationError if any required field is missing.
    Adds optional fields with default values if they are missing.
    """
    missing_fields = [col for col in REQUIRED_FIELDS if col not in df.columns]
    
    if missing_fields:
        raise SchemaValidationError(missing_fields)
        
    # Optional field defaults
    optional_defaults = {
        "carrier": "Unknown",
        "distance": 0.0,
        "cost": 0.0,
        "product": "Unknown Product",
        "invoice_amount": 0.0,
        "expected_delivery": pd.NaT,
        "actual_delivery": pd.NaT
    }
    
    for col, default_val in optional_defaults.items():
        if col not in df.columns:
            df[col] = default_val
            
    return df
