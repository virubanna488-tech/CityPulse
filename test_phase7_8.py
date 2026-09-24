"""
test_phase7_8.py - Automated Test Suite for Correlation Engine & Evidence Layer

Tests:
1. Multi-signal correlation clustering (co-occurring anomalies in same zone/window)
2. Full 'WHY THIS ALERT?' schema conformity (all 8 audit questions populated)
3. Non-causation integrity (prohibits causal assertions, enforces correlation wording)
4. Geographic isolation (correlations only form in Zone-B; zero false alerts in Zones A, C, D, E, F)
"""

import sys
import os
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from analytics.rolling import compute_rolling_metrics
from analytics.anomaly import detect_anomalies
from correlation.correlation_engine import build_correlation_clusters

def test_multi_signal_correlation():
    print("\n--- Test 1: Multi-Signal Correlation Clustering ---")
    df = pd.read_csv("data/processed/unified_civic_data.csv")
    df_roll = compute_rolling_metrics(df, window_minutes=15)
    df_anom = detect_anomalies(df_roll)
    
    alerts = build_correlation_clusters(df_anom, time_window_minutes=20, min_signals=2)
    assert len(alerts) > 0, "Should generate at least 1 correlated alert during storm scenario"
    
    # Check that each alert has at least 2 distinct signals
    for alert in alerts:
        assert alert["signals_count"] >= 2, "Alert must fuse at least 2 distinct signals"
        assert len(alert["evidence_points"]) >= 2, "Must contain at least 2 evidence points"
        
    print(f"Passed! Successfully formed {len(alerts)} multi-signal correlated alerts.")

def test_why_this_alert_schema():
    print("\n--- Test 2: 'WHY THIS ALERT?' Schema & Quantitative Evidence ---")
    df = pd.read_csv("data/processed/unified_civic_data.csv")
    df_roll = compute_rolling_metrics(df, window_minutes=15)
    df_anom = detect_anomalies(df_roll)
    alerts = build_correlation_clusters(df_anom, time_window_minutes=20)
    
    primary = alerts[0]
    why = primary["why_this_alert"]
    
    required_keys = [
        "question_1_what_changed",
        "question_2_where",
        "question_3_when",
        "question_4_signals_involved",
        "question_5_evidence",
        "question_6_why_unusual",
        "question_7_confidence",
        "question_8_data_health",
        "relationship_statement"
    ]
    
    for k in required_keys:
        assert k in why, f"Missing key in why_this_alert: {k}"
        assert why[k] is not None, f"Value for {k} must not be None"
        
    assert len(why["question_5_evidence"]) >= 2, "Evidence list must contain quantitative observations"
    print("Passed! 'WHY THIS ALERT?' inspection structure fully populated with grounded evidence.")

def test_non_causation_language():
    print("\n--- Test 3: Non-Causation Language Audit ---")
    df = pd.read_csv("data/processed/unified_civic_data.csv")
    df_roll = compute_rolling_metrics(df, window_minutes=15)
    df_anom = detect_anomalies(df_roll)
    alerts = build_correlation_clusters(df_anom)
    
    forbidden_words = ["caused the", "proves that", "definite cause", "direct causation"]
    required_concepts = ["correlation", "possible", "relationship"]
    
    for alert in alerts:
        rel_text = alert["why_this_alert"]["relationship_statement"].lower()
        headline_text = alert["headline"].lower()
        
        for bad in forbidden_words:
            assert bad not in rel_text, f"Forbidden causal phrasing found in statement: {bad}"
            assert bad not in headline_text, f"Forbidden causal phrasing found in headline: {bad}"
            
        has_required = any(req in rel_text for req in required_concepts)
        assert has_required, "Relationship statement must use cautious correlation terminology"
        
    print("Passed! Non-causation phrasing strictly adhered to across all alerts.")

def test_geographic_isolation():
    print("\n--- Test 4: Geographic Isolation & Jaipur Coordinates ---")
    df = pd.read_csv("data/processed/unified_civic_data.csv")
    df_roll = compute_rolling_metrics(df, window_minutes=15)
    df_anom = detect_anomalies(df_roll)
    alerts = build_correlation_clusters(df_anom)
    
    for alert in alerts:
        # All alerts must be in Zone-B
        assert alert["zone"] == "Zone-B", f"Unexpected alert in zone: {alert['zone']}"
        # Latitude must be within Jaipur range [26.8, 27.0]
        assert 26.8 <= alert["latitude"] <= 27.0, f"Latitude not in Jaipur range: {alert['latitude']}"
        assert 75.7 <= alert["longitude"] <= 75.9, f"Longitude not in Jaipur range: {alert['longitude']}"
        
    print("Passed! 100% of correlations isolated to Zone-B with verified Jaipur coordinates.")

if __name__ == "__main__":
    print("==================================================")
    print(">>> RUNNING PHASE 7 & 8 TEST SUITE <<<")
    print("==================================================")
    test_multi_signal_correlation()
    test_why_this_alert_schema()
    test_non_causation_language()
    test_geographic_isolation()
    print("\n==================================================")
    print(">>> ALL 4 PHASE 7 & 8 TESTS PASSED (100%) <<<")
    print("==================================================")
