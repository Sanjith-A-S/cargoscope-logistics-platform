import pandas as pd
from typing import Dict

def apply_schema_mapping(df: pd.DataFrame, mapping: Dict[str, str]) -> pd.DataFrame:
    """
    Apply detected mappings to the dataframe.
    """
    df = df.rename(columns=mapping)
    return df
