"""
test_phase13.py - Comprehensive Test Suite for Grounded Summary & Fallback System

Tests (A through I):
A. Normal city baseline narrative
B. Single anomaly detected
C. Multiple anomalies across feeds
D. Correlation / evidence present with non-causal disclaimer
E. Missing feed limitation handling
F. Empty evidence / cold start
G. Invalid / empty LLM response handling
H. Fallback activation when LLM fails
I. Unsupported factual content (anti-hallucination validation)
"""

import sys
import os
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from summary.summary_generator import (
    build_summary_context,
    generate_deterministic_summary,
    validate_summary,
    generate_citypulse_summary,
    GroundedLLMAdapter
)
from utils.geo_utils import CITY_NAME

def test_a_normal_city():
    print("\n--- Test A: Normal City Baseline Narrative ---")
    normal_context = {
        "city_name": CITY_NAME,
        "city_pulse_state": "NORMAL",
        "city_pulse_score": 10.0,
        "affected_zones": [],
        "anomaly_types": [],
        "evidence_items": [],
        "feed_limitations": []
    }
    summary = generate_deterministic_summary(normal_context)
    assert "NORMAL" in summary["narrative"]
    assert "standard baseline" in summary["narrative"]
    assert summary["grounded"] is True
    print(f"Passed! Normal narrative verified:\n   \"{summary['narrative']}\"")

def test_b_single_anomaly():
    print("\n--- Test B: Single Anomaly Detected ---")
    attn_context = {
        "city_name": CITY_NAME,
        "city_pulse_state": "ATTENTION",
        "city_pulse_score": 35.0,
        "affected_zones": ["Zone-A"],
        "affected_zone_labels": ["Zone-A (Walled City)"],
        "anomaly_types": ["RAINFALL_SURGE"],
        "evidence_items": ["Rainfall rate 22.0 mm/h"],
        "feed_limitations": []
    }
    summary = generate_deterministic_summary(attn_context)
    assert "ATTENTION" in summary["narrative"]
    assert "Zone-A" in summary["narrative"]
    assert "Rainfall Surge" in summary["narrative"]
    print("Passed! Single-anomaly narrative correctly reflects Zone-A and Rainfall Surge.")

def test_c_multiple_anomalies():
    print("\n--- Test C: Multiple Anomalies Across Feeds ---")
    elev_context = {
        "city_name": CITY_NAME,
        "city_pulse_state": "ELEVATED",
        "city_pulse_score": 55.0,
        "affected_zones": ["Zone-B"],
        "affected_zone_labels": ["Zone-B (MI Road Corridor)"],
        "anomaly_types": ["RAINFALL_SURGE", "TRAFFIC_SLOWDOWN", "TRANSIT_DELAY_SPIKE"],
        "evidence_items": ["Speed 12 km/h", "Delay 30 min"],
        "feed_limitations": []
    }
    summary = generate_deterministic_summary(elev_context)
    assert "ELEVATED" in summary["narrative"]
    assert "Zone-B" in summary["narrative"]
    assert "Traffic Slowdown" in summary["narrative"]
    print("Passed! Multiple-signal narrative verified.")

def test_d_correlation_and_evidence():
    print("\n--- Test D: Correlation Present with Non-Causal Grounding ---")
    context = {
        "city_name": CITY_NAME,
        "city_pulse_state": "ELEVATED",
        "city_pulse_score": 55.0,
        "affected_zones": ["Zone-B"],
        "affected_zone_labels": ["Zone-B (MI Road Corridor)"],
        "anomaly_types": ["RAINFALL_SURGE", "TRAFFIC_SLOWDOWN", "COMPLAINT_SPIKE"],
        "alert_ids": ["CP-ALERT-101"],
        "evidence_items": [
            "Rainfall peaked at 70.5 mm/h",
            "Speed dropped to 10.9 km/h",
            "12 complaints filed"
        ],
        "feed_limitations": []
    }
    summary = generate_deterministic_summary(context)
    assert "possible relationship" in summary["narrative"]
    assert "caused" not in summary["narrative"]
    assert "CP-ALERT-101" in summary["evidence_ids"]
    assert len(summary["evidence_points"]) == 3
    print("Passed! Non-causal terminology and empirical evidence traceability confirmed.")

def test_e_missing_feed():
    print("\n--- Test E: Missing Feed Limitation Handling ---")
    context_with_limit = {
        "city_name": CITY_NAME,
        "city_pulse_state": "NORMAL",
        "city_pulse_score": 10.0,
        "affected_zones": [],
        "anomaly_types": [],
        "evidence_items": [],
        "feed_limitations": ["Complaints feed is currently unavailable"]
    }
    summary = generate_deterministic_summary(context_with_limit)
    assert "Complaints feed is currently unavailable" in summary["narrative"]
    print("Passed! Data limitations transparently declared in narrative.")

def test_f_empty_evidence():
    print("\n--- Test F: Empty Evidence / Cold-Start Safety ---")
    summary = generate_citypulse_summary(
        city_pulse={},
        zone_pulses=[],
        active_anomalies=pd.DataFrame(),
        correlated_alerts=[],
        feed_health={}
    )
    assert "NORMAL" in summary["narrative"]
    assert summary["grounded"] is True
    print("Passed! Empty evidence safely defaults to NORMAL baseline.")

def test_g_and_h_llm_failure_and_fallback_activation():
    print("\n--- Test G & H: LLM Failure & Automatic Fallback Activation ---")
    # Adapter without API key
    adapter = GroundedLLMAdapter()
    assert adapter.is_available() is False, "Adapter should report unavailable without API key"
    
    mock_context = {
        "city_name": CITY_NAME,
        "city_pulse_state": "CRITICAL",
        "city_pulse_score": 95.0,
        "affected_zones": ["Zone-B"],
        "affected_zone_labels": ["Zone-B (MI Road)"],
        "anomaly_types": ["RAINFALL_SURGE", "TRAFFIC_SLOWDOWN"],
        "evidence_items": [],
        "feed_limitations": []
    }
    # Should automatically fall back to deterministic engine
    res = adapter.generate_summary(mock_context)
    assert "CRITICAL" in res["narrative"]
    assert "deterministic" in res["generated_by"]
    print(f"Passed! Fallback cleanly activated: {res['generated_by']}")

def test_i_unsupported_factual_content_rejection():
    print("\n--- Test I: Unsupported Content / Hallucination Validator ---")
    context = {
        "city_name": "Jaipur",
        "city_pulse_state": "ELEVATED",
        "affected_zones": ["Zone-B"]
    }
    
    # 1. Hallucinated unaffected zone (Zone-C)
    hallucinated_zone = "City status is ELEVATED. Severe flooding in Zone-C has caused major issues."
    valid_z, reason_z = validate_summary(hallucinated_zone, context)
    assert valid_z is False
    assert "Hallucinated unaffected zone" in reason_z
    
    # 2. Forbidden causal assertion
    causal_text = "City status is ELEVATED. Heavy rainfall caused the massive traffic congestion."
    valid_c, reason_c = validate_summary(causal_text, context)
    assert valid_c is False
    assert "Forbidden causal phrase" in reason_c
    
    # 3. External city hallucination
    external_city = "City status is ELEVATED in Delhi near the central market."
    valid_city, reason_city = validate_summary(external_city, context)
    assert valid_city is False
    assert "Hallucinated external city" in reason_city
    
    # 4. Valid summary
    valid_text = "Overall civic health is ELEVATED in Jaipur. Anomalies in Zone-B indicate a possible relationship between signals."
    is_ok, _ = validate_summary(valid_text, context)
    assert is_ok is True
    
    print("Passed! Anti-hallucination validator rejected causal claims and hallucinated zones/cities.")

if __name__ == "__main__":
    print("==================================================")
    print(">>> RUNNING PHASE 13 SUMMARY TEST SUITE <<<")
    print("==================================================")
    test_a_normal_city()
    test_b_single_anomaly()
    test_c_multiple_anomalies()
    test_d_correlation_and_evidence()
    test_e_missing_feed()
    test_f_empty_evidence()
    test_g_and_h_llm_failure_and_fallback_activation()
    test_i_unsupported_factual_content_rejection()
    print("\n==================================================")
    print(">>> ALL 9 PHASE 13 TESTS PASSED (100%) <<<")
    print("==================================================")
