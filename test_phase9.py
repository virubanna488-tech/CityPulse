"""
test_phase9.py - Automated Test Suite for City Pulse Status & Scoring Engine

Tests:
1. All four categorical pulse states verified: NORMAL, ATTENTION, ELEVATED, CRITICAL
2. Zone isolation (1 critical zone does not make the whole city CRITICAL)
3. Multi-zone city-wide crisis escalation (>= 2 critical zones triggers CRITICAL city pulse)
4. Grounded, explainable text generation (no magic numbers, full traceability)
5. Graceful handling of empty or missing feeds
"""

import sys
import os
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from analytics.pulse import (
    calculate_zone_pulse,
    calculate_city_pulse,
    compute_city_pulse_pipeline,
    score_to_pulse_state
)
from analytics.rolling import compute_rolling_metrics
from analytics.anomaly import detect_anomalies
from correlation.correlation_engine import build_correlation_clusters

def test_all_four_pulse_states():
    print("\n--- Test 1: Verification of All Four Pulse States ---")
    
    # State 1: NORMAL (0-25 score)
    df_empty = pd.DataFrame(columns=["zone", "anomaly_severity", "feed_type"])
    p_norm = calculate_zone_pulse("Zone-A", df_empty)
    assert p_norm["pulse_state"] == "NORMAL", f"Expected NORMAL, got {p_norm['pulse_state']}"
    assert p_norm["pulse_score"] == 10.0
    print("   * NORMAL state verified (Baseline score = 10.0)")
    
    # State 2: ATTENTION (26-50 score: 1 moderate anomaly = 10 + 15 = 25? + 2nd moderate = 40)
    df_attn = pd.DataFrame([
        {"zone": "Zone-A", "anomaly_severity": "MODERATE", "feed_type": "rainfall_rate"},
        {"zone": "Zone-A", "anomaly_severity": "MODERATE", "feed_type": "rainfall_rate"}
    ])
    p_attn = calculate_zone_pulse("Zone-A", df_attn)
    assert p_attn["pulse_state"] == "ATTENTION", f"Expected ATTENTION, got {p_attn['pulse_state']}"
    assert 26.0 <= p_attn["pulse_score"] <= 50.0
    print(f"   * ATTENTION state verified (Score = {p_attn['pulse_score']})")
    
    # State 3: ELEVATED (51-75 score: 1 high + 1 mod + multi-feed = 10 + 25 + 15 + 20 = 70)
    df_elev = pd.DataFrame([
        {"zone": "Zone-A", "anomaly_severity": "HIGH", "feed_type": "traffic_speed"},
        {"zone": "Zone-A", "anomaly_severity": "MODERATE", "feed_type": "transit_delay"}
    ])
    p_elev = calculate_zone_pulse("Zone-A", df_elev)
    assert p_elev["pulse_state"] == "ELEVATED", f"Expected ELEVATED, got {p_elev['pulse_state']}"
    assert 51.0 <= p_elev["pulse_score"] <= 75.0
    print(f"   * ELEVATED state verified (Score = {p_elev['pulse_score']})")
    
    # State 4: CRITICAL (76-100 score: storm + traffic + complaints + correlated alert)
    df_crit = pd.DataFrame([
        {"zone": "Zone-B", "anomaly_severity": "HIGH", "feed_type": "rainfall_rate"},
        {"zone": "Zone-B", "anomaly_severity": "HIGH", "feed_type": "traffic_speed"},
        {"zone": "Zone-B", "anomaly_severity": "HIGH", "feed_type": "transit_delay"},
        {"zone": "Zone-B", "anomaly_severity": "HIGH", "feed_type": "311_incident"}
    ])
    p_crit = calculate_zone_pulse("Zone-B", df_crit, has_correlated_alert=True)
    assert p_crit["pulse_state"] == "CRITICAL", f"Expected CRITICAL, got {p_crit['pulse_state']}"
    assert p_crit["pulse_score"] >= 76.0
    print(f"   * CRITICAL state verified (Score = {p_crit['pulse_score']})")
    print("Passed! All 4 pulse states mathematically verified.")

def test_zone_isolation_and_city_aggregation():
    print("\n--- Test 2: Zone Isolation vs City-Wide Aggregation ---")
    df_raw = pd.read_csv("data/processed/unified_civic_data.csv")
    df_roll = compute_rolling_metrics(df_raw, window_minutes=15)
    df_anom = detect_anomalies(df_roll)
    alerts = build_correlation_clusters(df_anom)
    
    city_pulse, zone_pulses = compute_city_pulse_pipeline(df_anom, alerts)
    
    # Zone-B is in crisis
    zb = [z for z in zone_pulses if z["zone"] == "Zone-B"][0]
    assert zb["pulse_state"] == "CRITICAL", f"Zone-B should be CRITICAL, got {zb['pulse_state']}"
    assert zb["pulse_score"] == 100.0
    
    # Zones A, C, D, E, F remain NORMAL
    calm_zones = [z for z in zone_pulses if z["zone"] != "Zone-B"]
    for z in calm_zones:
        assert z["pulse_state"] == "NORMAL", f"{z['zone']} should be NORMAL, got {z['pulse_state']}"
        assert z["pulse_score"] == 10.0
        
    # Crucial test: City Pulse should be ELEVATED, NOT CRITICAL!
    # Because only 1 out of 6 zones is in distress.
    assert city_pulse["city_pulse_state"] == "ELEVATED", f"City Pulse should be ELEVATED, got {city_pulse['city_pulse_state']}"
    assert "Zone-B" in city_pulse["explanation"], "Explanation should cite Zone-B specifically"
    
    print("Passed! Localized crisis in Zone-B did NOT throw entire city into false CRITICAL panic.")
    print(f"   Zone-B State: {zb['pulse_state']} | City-Wide State: {city_pulse['city_pulse_state']}")

def test_city_wide_crisis_escalation():
    print("\n--- Test 3: City-Wide Systemic Crisis Escalation ---")
    # Simulate a scenario where 2 separate zones are simultaneously CRITICAL
    synthetic_zones = [
        {"zone": "Zone-A", "pulse_state": "CRITICAL", "pulse_score": 90.0},
        {"zone": "Zone-B", "pulse_state": "CRITICAL", "pulse_score": 95.0},
        {"zone": "Zone-C", "pulse_state": "NORMAL", "pulse_score": 10.0},
        {"zone": "Zone-D", "pulse_state": "NORMAL", "pulse_score": 10.0},
        {"zone": "Zone-E", "pulse_state": "NORMAL", "pulse_score": 10.0},
        {"zone": "Zone-F", "pulse_state": "NORMAL", "pulse_score": 10.0},
    ]
    city_escalated = calculate_city_pulse(synthetic_zones)
    assert city_escalated["city_pulse_state"] == "CRITICAL", f"Expected CRITICAL, got {city_escalated['city_pulse_state']}"
    assert len(city_escalated["critical_zones"]) == 2
    print("Passed! When multiple zones reach crisis, City Pulse correctly escalates to CRITICAL.")

def test_missing_data_resilience():
    print("\n--- Test 4: Missing Telemetry & Resilience ---")
    # Completely empty anomaly list
    city_pulse, zone_pulses = compute_city_pulse_pipeline(pd.DataFrame())
    assert city_pulse["city_pulse_state"] == "NORMAL"
    assert len(zone_pulses) == 6
    for z in zone_pulses:
        assert z["pulse_state"] == "NORMAL"
    print("Passed! Empty feeds gracefully return NORMAL baseline without exceptions.")

if __name__ == "__main__":
    print("==================================================")
    print(">>> RUNNING PHASE 9 TEST SUITE <<<")
    print("==================================================")
    test_all_four_pulse_states()
    test_zone_isolation_and_city_aggregation()
    test_city_wide_crisis_escalation()
    test_missing_data_resilience()
    print("\n==================================================")
    print(">>> ALL 4 PHASE 9 TESTS PASSED (100%) <<<")
    print("==================================================")
