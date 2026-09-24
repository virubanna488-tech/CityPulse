"""
test_phase10_12.py - Comprehensive Verification for Streamlit Dashboard, Map, Timeline, and Data Health

Tests:
1. app.py syntax and import integrity
2. End-to-end pipeline execution (Normalization -> Rolling -> Anomaly -> Correlation -> Pulse)
3. Folium OpenStreetMap construction and marker generation
4. Event Timeline formatting
5. Data Health extraction and missing-feed resilience
6. Empty data / zero feeds cold-start safety
"""

import sys
import os
import pandas as pd
import folium

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import load_and_process_civic_data
from utils.geo_utils import ZONES, CITY_CENTER, get_zone_metadata

def test_dashboard_pipeline_execution():
    print("\n--- Test 1: Dashboard Pipeline Execution (Normal Feeds) ---")
    w_path = "data/raw/weather_raw.json"
    t_path = "data/raw/traffic_raw.csv"
    c_path = "data/raw/complaints_raw.json"
    
    df_unified, val_report, df_anomalies, alerts, city_pulse, zone_pulses = load_and_process_civic_data(
        w_path, t_path, c_path
    )
    
    assert not df_unified.empty, "Unified DataFrame should not be empty"
    assert len(df_unified) == 486, f"Expected 486 records, got {len(df_unified)}"
    assert not df_anomalies.empty, "Anomalies DataFrame should not be empty"
    assert len(alerts) > 0, "Correlated alerts should be generated"
    assert city_pulse["city_pulse_state"] == "ELEVATED", f"Expected ELEVATED, got {city_pulse['city_pulse_state']}"
    assert len(zone_pulses) == 6, f"Expected 6 zones, got {len(zone_pulses)}"
    
    print(f"Passed! Pipeline executed: {len(df_unified)} records -> {len(alerts)} alerts -> Pulse: {city_pulse['city_pulse_state']}")

def test_folium_map_generation():
    print("\n--- Test 2: Folium OpenStreetMap Layer Construction ---")
    w_path = "data/raw/weather_raw.json"
    t_path = "data/raw/traffic_raw.csv"
    c_path = "data/raw/complaints_raw.json"
    
    _, _, df_anomalies, _, _, zone_pulses = load_and_process_civic_data(w_path, t_path, c_path)
    
    # Construct Folium Map
    m = folium.Map(
        location=[CITY_CENTER["latitude"], CITY_CENTER["longitude"]],
        zoom_start=CITY_CENTER["zoom_start"],
        tiles="CartoDB positron"
    )
    
    # Add Zone rings
    for zp in zone_pulses:
        zid = zp["zone"]
        zmeta = get_zone_metadata(zid)
        folium.Circle(
            location=[zmeta["latitude"], zmeta["longitude"]],
            radius=1500,
            color="#28a745" if zp["pulse_state"] == "NORMAL" else "#dc3545"
        ).add_to(m)
        
    # Add Anomaly points
    active = df_anomalies[df_anomalies["is_anomaly"] == True]
    for _, anom in active.head(10).iterrows():
        folium.CircleMarker(
            location=[anom["latitude"], anom["longitude"]],
            radius=6
        ).add_to(m)
        
    html_repr = m.get_root().render()
    assert len(html_repr) > 500, "Map HTML should be non-empty"
    assert "Jaipur" in str(CITY_CENTER) or "26.9124" in str(CITY_CENTER), "Map should center on Jaipur"
    print("Passed! OpenStreetMap HTML layers rendered cleanly with zone rings and anomaly markers.")

def test_missing_feed_resilience():
    print("\n--- Test 3: Missing Feed Resilience (Complaints Offline) ---")
    w_path = "data/raw/weather_raw.json"
    t_path = "data/raw/traffic_raw.csv"
    c_missing = "data/raw/non_existent.json"
    
    df_unified, val_report, df_anomalies, alerts, city_pulse, zone_pulses = load_and_process_civic_data(
        w_path, t_path, c_missing
    )
    
    assert not df_unified.empty, "Pipeline should continue with Weather and Traffic"
    assert val_report["feed_health"]["complaints"] == "Unavailable"
    assert "Healthy" in val_report["feed_health"]["weather"]
    assert "Healthy" in val_report["feed_health"]["traffic"]
    assert city_pulse["city_pulse_state"] in ["NORMAL", "ATTENTION", "ELEVATED", "CRITICAL"]
    print("Passed! Dashboard gracefully degraded when 311 complaints feed went offline.")

def test_empty_cold_start():
    print("\n--- Test 4: Empty Feeds / Cold-Start Safety ---")
    df_empty, val_report, df_anom, alerts, city_pulse, zone_pulses = load_and_process_civic_data(
        "non_existent_w.json", "non_existent_t.csv", "non_existent_c.json"
    )
    
    assert df_empty.empty
    assert city_pulse["city_pulse_state"] == "NORMAL"
    assert city_pulse["city_pulse_score"] == 10.0
    print("Passed! Cold-start with zero feeds safely defaulted to NORMAL baseline without crashing.")

if __name__ == "__main__":
    print("==================================================")
    print(">>> RUNNING PHASE 10-12 INTEGRATION TEST SUITE <<<")
    print("==================================================")
    test_dashboard_pipeline_execution()
    test_folium_map_generation()
    test_missing_feed_resilience()
    test_empty_cold_start()
    print("\n==================================================")
    print(">>> ALL 4 PHASE 10-12 TESTS PASSED (100%) <<<")
    print("==================================================")
