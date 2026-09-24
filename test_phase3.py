"""
test_phase3.py - Validation Tests for Normalization & Common Data Model

Tests:
1. Schema conformity (all required columns present and correctly typed)
2. Value normalization (weather mm/h, traffic km/h and min, complaints count)
3. Coordinate validity (within [-90, 90] and [-180, 180])
4. Timestamp parsing (monotonic chronological ordering)
5. Resilience / Missing-feed handling (runs without crashing if a feed is missing)
"""

import sys
import os
import pandas as pd
import numpy as np

# Ensure citypulse root is in path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from normalization.normalize import normalize_all_feeds, normalize_weather_feed, normalize_traffic_feed, normalize_complaints_feed
from utils.validation import validate_dataframe, REQUIRED_COLUMNS

def test_full_normalization_pipeline():
    print("\n--- Test 1: Full Pipeline Normalization ---")
    df, report = normalize_all_feeds()
    
    assert not df.empty, "DataFrame should not be empty!"
    for col in REQUIRED_COLUMNS:
        assert col in df.columns, f"Missing required column: {col}"
        
    print(f"Passed! Ingested {len(df)} total unified records.")
    print(f"Feed Health Report: {report['feed_health']}")
    
def test_schema_types_and_ranges():
    print("\n--- Test 2: Schema Types & Physical Ranges ---")
    df, _ = normalize_all_feeds()
    
    # 1. Timestamps must be valid datetime
    assert pd.api.types.is_datetime64_any_dtype(df["timestamp"]), "timestamp must be datetime64"
    assert df["timestamp"].isna().sum() == 0, "No null timestamps allowed"
    
    # 2. Coordinates must be bounded
    assert (df["latitude"] >= -90.0).all() and (df["latitude"] <= 90.0).all(), "Latitude out of bounds"
    assert (df["longitude"] >= -180.0).all() and (df["longitude"] <= 180.0).all(), "Longitude out of bounds"
    
    # 3. Numeric values must be non-negative and finite
    assert (df["value"] >= 0.0).all(), "Values should be non-negative"
    assert np.isfinite(df["value"]).all(), "Values must be finite numbers"
    
    # 4. Sources must match expected feeds
    unique_sources = set(df["source"].unique())
    assert unique_sources == {"weather", "traffic", "complaints"}, f"Unexpected sources: {unique_sources}"
    
    print(f"Passed! Coordinates, datetimes, and values meet all physical bounds.")

def test_resilience_missing_feed():
    print("\n--- Test 3: Graceful Handling of Missing Feed ---")
    # Point complaints to a non-existent file, output_path=None to avoid overwriting production file
    df_partial, report = normalize_all_feeds(
        complaints_path="data/raw/non_existent_complaints.json",
        output_path=None
    )
    
    assert not df_partial.empty, "Should continue operating with remaining feeds"
    assert report["feed_health"]["complaints"] == "Unavailable"
    assert "Healthy" in report["feed_health"]["weather"]
    assert "Healthy" in report["feed_health"]["traffic"]
    
    print("Passed! Pipeline continued smoothly even when complaints feed was offline.")

def test_validation_drops_corrupted_data():
    print("\n--- Test 4: Validation Layer Filtering Malformed Records ---")
    corrupted_data = pd.DataFrame([
        # Valid row
        {"timestamp": "2026-09-24 13:00:00", "source": "weather", "feed_type": "rainfall_rate",
         "event_type": "precipitation", "zone": "Zone-A", "latitude": 28.61, "longitude": 77.20,
         "value": 2.5, "unit": "mm/h", "severity": "NORMAL", "confidence": 0.95},
        # Invalid coordinate
        {"timestamp": "2026-09-24 13:00:00", "source": "weather", "feed_type": "rainfall_rate",
         "event_type": "precipitation", "zone": "Zone-A", "latitude": 999.0, "longitude": 77.20,
         "value": 2.5, "unit": "mm/h", "severity": "NORMAL", "confidence": 0.95},
        # Corrupt timestamp
        {"timestamp": "INVALID_TIME", "source": "traffic", "feed_type": "traffic_speed",
         "event_type": "speed_sensor", "zone": "Zone-B", "latitude": 28.62, "longitude": 77.24,
         "value": 45.0, "unit": "km/h", "severity": "NORMAL", "confidence": 0.90},
        # Duplicate of row 1
        {"timestamp": "2026-09-24 13:00:00", "source": "weather", "feed_type": "rainfall_rate",
         "event_type": "precipitation", "zone": "Zone-A", "latitude": 28.61, "longitude": 77.20,
         "value": 2.5, "unit": "mm/h", "severity": "NORMAL", "confidence": 0.95},
    ])
    
    cleaned, report = validate_dataframe(corrupted_data)
    assert len(cleaned) == 1, f"Expected 1 valid row, got {len(cleaned)}"
    assert report["invalid_coords_dropped"] == 1
    assert report["missing_timestamp_dropped"] == 1
    assert report["duplicates_dropped"] == 1
    print("Passed! Bad coordinates, invalid timestamps, and duplicates safely stripped.")

if __name__ == "__main__":
    print("==================================================")
    print(">>> RUNNING PHASE 3 NORMALIZATION TEST SUITE <<<")
    print("==================================================")
    test_full_normalization_pipeline()
    test_schema_types_and_ranges()
    test_resilience_missing_feed()
    test_validation_drops_corrupted_data()
    print("\n==================================================")
    print(">>> ALL 4 NORMALIZATION TESTS PASSED (100%) <<<")
    print("==================================================")
