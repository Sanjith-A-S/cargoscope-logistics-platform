import pandas as pd
from rapidfuzz import process, fuzz
import numpy as np

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the ingested trade data.
    - Remove duplicates
    - Handle missing values
    - Convert date formats
    - Normalize customer names using RapidFuzz
    """
    df_clean = df.copy()
    
    # 1. Remove strict duplicates
    df_clean = df_clean.drop_duplicates(subset=['shipment_id'])
    
    # 2. Date conversions
    date_cols = ['order_date', 'expected_delivery', 'actual_delivery']
    for col in date_cols:
        if col in df_clean.columns:
            df_clean[col] = pd.to_datetime(df_clean[col], errors='coerce')
            
    # 3. Handle missing values
    # Fill missing carrier with 'Unknown'
    if 'carrier' in df_clean.columns:
        df_clean['carrier'] = df_clean['carrier'].fillna('Unknown')
    
    # Calculate delivery metrics safely
    has_actual = df_clean['actual_delivery'].notna()
    df_clean.loc[has_actual, 'is_delayed'] = df_clean.loc[has_actual, 'actual_delivery'] > df_clean.loc[has_actual, 'expected_delivery']
    df_clean['is_delayed'] = df_clean['is_delayed'].fillna(False).astype(bool)
    
    status_mask = df_clean['status'].isna()
    df_clean.loc[status_mask & has_actual, 'status'] = 'Delivered'
    df_clean.loc[status_mask & ~has_actual, 'status'] = 'In Transit'
    
    # 4. Normalize Customer Names using RapidFuzz
    # E.g. "Apple" and "Apple Inc"
    unique_customers = df_clean['customer'].dropna().unique().tolist()
    normalized_map = {}
    
    # Simple clustering: if similarity > 90, map to the shortest version
    processed = set()
    for cust in unique_customers:
        if cust in processed:
            continue
        # Find matches
        matches = process.extract(cust, unique_customers, scorer=fuzz.WRatio, limit=10)
        similar = [m[0] for m in matches if m[1] >= 90]
        
        # Pick representative (e.g. shortest name)
        if similar:
            representative = min(similar, key=len)
            for s in similar:
                normalized_map[s] = representative
                processed.add(s)
        else:
            normalized_map[cust] = cust
            processed.add(cust)
            
    df_clean['customer'] = df_clean['customer'].map(normalized_map).fillna('Unknown Customer')
    
    return df_clean
