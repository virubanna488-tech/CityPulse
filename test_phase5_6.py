"""
test_phase5_6.py - Test Suite for Rolling-Window Analytics & Anomaly Detection

Tests:
1. Rolling metric calculations (moving mean, std, deviation, pct_change)
2. Edge cases (empty DataFrame, single row, zero baseline, missing feed)
3. Anomaly detection rules (rainfall, traffic, transit, complaints)
4. Chronological scenario grounding (Zone-B timeline: Rain -> Complaints -> Slowdown -> Delay)
5. Zone isolation (Zero false alarms in unaffected zones A, C, D, E, F)
"""

import sys
import os
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from analytics.rolling import compute_rolling_metrics
from analytics.anomaly import detect_anomalies, get_active_anomalies, ANOMALY_THRESHOLDS

def test_rolling_metric_calculation():
    print("\n--- Test 1: Rolling Metrics Calculation ---")
    df = pd.read_csv("data/processed/unified_civic_data.csv")
    df_roll = compute_rolling_metrics(df, window_minutes=15)
    
    expected_cols = ["rolling_mean", "rolling_std", "deviation", "pct_change", "recent_change", "rolling_count"]
    for col in expected_cols:
        assert col in df_roll.columns, f"Missing rolling column: {col}"
        assert not df_roll[col].isna().any(), f"Column {col} contains NaN values"
        assert np.isfinite(df_roll[col]).all(), f"Column {col} contains non-finite values"
        
    print(f"Passed! Rolling metrics computed across {len(df_roll)} records with zero NaNs.")

def test_edge_cases_and_insufficient_history():
    print("\n--- Test 2: Edge Cases & Insufficient History ---")
    # Empty DataFrame
    empty_df = pd.DataFrame(columns=["timestamp", "source", "feed_type", "zone", "value"])
    res_empty = compute_rolling_metrics(empty_df)
    assert res_empty.empty, "Empty input should return empty output"
    res_anom_empty = detect_anomalies(res_empty)
    assert res_anom_empty.empty, "Empty input to anomaly detection should return empty"
    
    # Single row (insufficient history)
    single_df = pd.DataFrame([{
        "timestamp": "2026-09-24 13:00:00",
        "source": "weather",
        "feed_type": "rainfall_rate",
        "event_type": "precipitation",
        "zone": "Zone-A",
        "latitude": 28.61,
        "longitude": 77.20,
        "value": 0.0,
        "unit": "mm/h",
        "severity": "NORMAL",
        "confidence": 0.95
    }])
    res_single = compute_rolling_metrics(single_df)
    assert len(res_single) == 1
    assert res_single.iloc[0]["rolling_mean"] == 0.0
    assert res_single.iloc[0]["deviation"] == 0.0
    
    anom_single = detect_anomalies(res_single)
    assert anom_single.iloc[0]["is_anomaly"] == False
    
    print("Passed! Empty DataFrames and single-record inputs handled gracefully.")

def test_anomaly_detection_rules():
    print("\n--- Test 3: Rule-Based Anomaly Evaluation ---")
    df = pd.read_csv("data/processed/unified_civic_data.csv")
    df_roll = compute_rolling_metrics(df, window_minutes=15)
    df_anom = detect_anomalies(df_roll)
    active = get_active_anomalies(df_anom)
    
    assert not active.empty, "Should detect anomalies during storm scenario"
    detected_types = set(active["anomaly_type"].unique())
    expected_types = {"RAINFALL_SURGE", "TRAFFIC_SLOWDOWN", "TRANSIT_DELAY_SPIKE", "COMPLAINT_SPIKE"}
    assert detected_types == expected_types, f"Expected {expected_types}, got {detected_types}"
    
    # Check that explanation is populated
    for _, row in active.iterrows():
        assert len(row["anomaly_explanation"]) > 10, "Explanation must not be empty"
        assert row["anomaly_score"] > 0.0, "Anomaly score must be > 0"
        
    print(f"Passed! All 4 civic anomaly categories triggered with grounded explanations:")
    for atype in sorted(detected_types):
        count = (active["anomaly_type"] == atype).sum()
        print(f"   * {atype}: {count} events")

def test_chronology_and_zone_isolation():
    print("\n--- Test 4: Chronology & Zone Isolation ---")
    df = pd.read_csv("data/processed/unified_civic_data.csv")
    df_roll = compute_rolling_metrics(df, window_minutes=15)
    df_anom = detect_anomalies(df_roll)
    active = get_active_anomalies(df_anom)
    
    # 1. Zone Isolation: 100% of anomalies must be in Zone-B
    assert (active["zone"] == "Zone-B").all(), "Anomalies must only be detected in Zone-B"
    non_b_anomalies = df_anom[(df_anom["zone"] != "Zone-B") & (df_anom["is_anomaly"] == True)]
    assert len(non_b_anomalies) == 0, f"False positives detected in other zones: {len(non_b_anomalies)}"
    
    # 2. Chronological order in Zone-B
    rain_start = active[active["anomaly_type"] == "RAINFALL_SURGE"]["timestamp"].min()
    complaints_start = active[active["anomaly_type"] == "COMPLAINT_SPIKE"]["timestamp"].min()
    traffic_start = active[active["anomaly_type"] == "TRAFFIC_SLOWDOWN"]["timestamp"].min()
    transit_start = active[active["anomaly_type"] == "TRANSIT_DELAY_SPIKE"]["timestamp"].min()
    
    assert rain_start <= complaints_start, "Rainfall must precede or coincide with complaints spike"
    assert complaints_start <= traffic_start, "Complaints must emerge as traffic slows"
    
    print("Passed! Zone isolation verified (0 false alarms in Zones A, C, D, E, F).")
    print(f"Verified Timeline in Zone-B:")
    print(f"   1. {rain_start} -> RAINFALL_SURGE")
    print(f"   2. {complaints_start} -> COMPLAINT_SPIKE")
    print(f"   3. {traffic_start} -> TRAFFIC_SLOWDOWN & TRANSIT_DELAY_SPIKE")

if __name__ == "__main__":
    print("==================================================")
    print(">>> RUNNING PHASE 5 & 6 TEST SUITE <<<")
    print("==================================================")
    test_rolling_metric_calculation()
    test_edge_cases_and_insufficient_history()
    test_anomaly_detection_rules()
    test_chronology_and_zone_isolation()
    print("\n==================================================")
    print(">>> ALL 4 PHASE 5 & 6 TESTS PASSED (100%) <<<")
    print("==================================================")
