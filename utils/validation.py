"""
validation.py - Data Validation and Sanity Rules for CityPulse

Ensures normalized records adhere to schema integrity:
- Valid timestamps
- Coordinates within realistic bounds
- Positive/finite numeric values
- Absence of duplicates
"""

import pandas as pd
import numpy as np

REQUIRED_COLUMNS = [
    "timestamp",
    "source",
    "feed_type",
    "event_type",
    "zone",
    "latitude",
    "longitude",
    "value",
    "unit",
    "severity",
    "confidence"
]

def validate_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Validates a normalized DataFrame and removes malformed rows.
    Returns:
        (cleaned_df, validation_report)
    """
    report = {
        "initial_rows": len(df),
        "missing_timestamp_dropped": 0,
        "invalid_coords_dropped": 0,
        "invalid_value_dropped": 0,
        "duplicates_dropped": 0,
        "final_valid_rows": 0,
        "is_healthy": True
    }
    
    if df.empty:
        report["is_healthy"] = False
        return df, report
        
    # Check for missing required columns
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Normalized DataFrame is missing required columns: {missing_cols}")
        
    cleaned = df.copy()
    
    # 1. Validate timestamps
    cleaned["timestamp"] = pd.to_datetime(cleaned["timestamp"], errors="coerce")
    null_ts = cleaned["timestamp"].isna()
    report["missing_timestamp_dropped"] = int(null_ts.sum())
    cleaned = cleaned[~null_ts]
    
    # 2. Validate coordinates
    valid_coords = (
        cleaned["latitude"].between(-90.0, 90.0) &
        cleaned["longitude"].between(-180.0, 180.0) &
        cleaned["latitude"].notna() &
        cleaned["longitude"].notna()
    )
    report["invalid_coords_dropped"] = int((~valid_coords).sum())
    cleaned = cleaned[valid_coords]
    
    # 3. Validate numeric value
    cleaned["value"] = pd.to_numeric(cleaned["value"], errors="coerce")
    valid_vals = cleaned["value"].notna() & np.isfinite(cleaned["value"])
    report["invalid_value_dropped"] = int((~valid_vals).sum())
    cleaned = cleaned[valid_vals]
    
    # 4. Remove duplicate entries
    before_dedup = len(cleaned)
    cleaned = cleaned.drop_duplicates(subset=["timestamp", "source", "feed_type", "zone", "event_type"])
    report["duplicates_dropped"] = before_dedup - len(cleaned)
    
    report["final_valid_rows"] = len(cleaned)
    report["is_healthy"] = report["final_valid_rows"] > 0
    
    return cleaned.reset_index(drop=True), report
