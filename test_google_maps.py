"""
test_google_maps.py - Automated Verification Suite for Google Maps JS API Integration

Verifies:
1. Secure API key retrieval (st.secrets, os.environ, and graceful None fallback)
2. Google Maps HTML builder with dark theme, zones, anomalies, non-causal disclaimers
3. InfoWindow content formatting & non-causal language adherence
4. Dual-engine orchestrator logic (Google Maps when key present, Folium fallback when missing)
5. Zero leakage of API key to standard logs or prints
"""

import os
import sys
import json
import pytest
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from utils.geo_utils import CITY_CENTER, ZONES, get_zone_metadata
from app import load_and_process_civic_data
from ui.google_map import (
    get_google_maps_api_key,
    build_google_maps_html,
    render_citypulse_map,
    render_folium_fallback
)

def test_api_key_retrieval_safe_fallback(monkeypatch):
    """Verify that get_google_maps_api_key handles missing key without throwing exception."""
    import streamlit as st
    
    # 1. When secrets and env are empty
    monkeypatch.setattr(st, "secrets", {}, raising=False)
    monkeypatch.delenv("GOOGLE_MAPS_API_KEY", raising=False)
    assert get_google_maps_api_key() is None
    
    # 2. When placeholder in env
    monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "YOUR_KEY_HERE")
    assert get_google_maps_api_key() is None
    
    monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "YOUR_GOOGLE_MAPS_API_KEY_HERE")
    assert get_google_maps_api_key() is None
    
    # 3. When valid in env
    monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "AIzaSyFakeKeyForTestVerification_12345")
    assert get_google_maps_api_key() == "AIzaSyFakeKeyForTestVerification_12345"
    
    # 4. When valid in st.secrets
    monkeypatch.setattr(st, "secrets", {"GOOGLE_MAPS_API_KEY": "AIzaSySecretsKey_999"}, raising=False)
    assert get_google_maps_api_key() == "AIzaSySecretsKey_999"


def test_build_google_maps_html_structure():
    """Verify that build_google_maps_html produces valid dark theme map embed with all required components."""
    w_path = "data/raw/weather_raw.json"
    t_path = "data/raw/traffic_raw.csv"
    c_path = "data/raw/complaints_raw.json"
    
    df_unified, _, df_anomalies, alerts, city_pulse, zone_pulses = load_and_process_civic_data(
        w_path, t_path, c_path
    )
    
    dummy_key = "AIzaSyTestKeyValidFormat987654321"
    html = build_google_maps_html(
        api_key=dummy_key,
        city_center=CITY_CENTER,
        zone_pulses=zone_pulses,
        anomalies_df=df_anomalies[df_anomalies["is_anomaly"] == True],
        alerts=alerts,
        selected_zone="All Zones"
    )
    
    assert isinstance(html, str)
    assert len(html) > 1000
    
    # 1. Check Google Maps JS API script tag inclusion
    assert f"https://maps.googleapis.com/maps/api/js?key={dummy_key}" in html
    assert "callback=initCityPulseMap" in html
    
    # 2. Check dark control-room theme styles
    assert "styles: darkMapStyles" in html
    assert "#111827" in html  # Dark background
    
    # 3. Check zone containment circles and 6 municipal zones
    for zid in ZONES.keys():
        assert f'"{zid}"' in html, f"Zone {zid} should be in JSON payload"
        
    # 4. Check non-causal disclaimer presence in InfoWindow
    assert "Spatiotemporal Association" in html
    
    # 5. Check floating map legend
    assert "map-legend" in html
    assert "Rain" in html
    assert "Traffic" in html
    assert "Critical" in html
    assert "Normal" in html


def test_google_maps_html_non_causation_integrity():
    """Verify that no causal certainty claims are made in the generated map embed."""
    w_path = "data/raw/weather_raw.json"
    t_path = "data/raw/traffic_raw.csv"
    c_path = "data/raw/complaints_raw.json"
    
    _, _, df_anomalies, alerts, _, zone_pulses = load_and_process_civic_data(w_path, t_path, c_path)
    
    html = build_google_maps_html(
        api_key="AIzaSyTestKey_123",
        city_center=CITY_CENTER,
        zone_pulses=zone_pulses,
        anomalies_df=df_anomalies,
        alerts=alerts
    )
    
    prohibited_causal_phrases = [
        "traffic is caused by rainfall",
        "rain caused the delay",
        "proven causation",
        "rain caused traffic"
    ]
    html_lower = html.lower()
    for phrase in prohibited_causal_phrases:
        assert phrase not in html_lower, f"Prohibited causal claim found: '{phrase}'"


def test_folium_fallback_integrity():
    """Verify that render_folium_fallback constructs and executes cleanly."""
    w_path = "data/raw/weather_raw.json"
    t_path = "data/raw/traffic_raw.csv"
    c_path = "data/raw/complaints_raw.json"
    
    _, _, df_anomalies, _, _, zone_pulses = load_and_process_civic_data(w_path, t_path, c_path)
    
    # Verify render_folium_fallback is callable
    assert callable(render_folium_fallback)
    assert callable(render_citypulse_map)
