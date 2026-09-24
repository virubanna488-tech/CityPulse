"""
app.py - CityPulse Live Civic Health Dashboard (Jaipur)

A real-time civic health monitoring system that fuses municipal weather sensors,
traffic corridors, and 311 citizen incident complaints into one clear "pulse".

Built for AMIHACKS 1.0 Hackathon.
Demonstration city: Jaipur, Rajasthan.
"""

import sys
import os
from datetime import datetime
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium

# Ensure project root is on Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from utils.geo_utils import ZONES, CITY_CENTER, CITY_NAME, get_zone_metadata
from normalization.normalize import normalize_all_feeds
from analytics.rolling import compute_rolling_metrics
from analytics.anomaly import detect_anomalies, get_active_anomalies
from correlation.correlation_engine import build_correlation_clusters
from analytics.pulse import compute_city_pulse_pipeline
from summary.summary_generator import generate_citypulse_summary

from ui.styles import get_custom_css
from ui.google_map import render_citypulse_map, get_google_maps_api_key
from ui.components import (
    render_header,
    render_demo_notice,
    render_hero_pulse,
    render_kpi_cards,
    render_narrative_card,
    render_active_anomalies_section,
    render_evidence_explorer_section,
    render_zone_grid,
    render_timeline,
    render_data_health
)

# ---------------------------------------------------------
# Page Configuration & Clean Dark Theme Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="CityPulse — Live Civic Health Dashboard",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject dark control-room custom CSS
st.markdown(get_custom_css(), unsafe_allow_html=True)

# ---------------------------------------------------------
# Data Pipeline Caching / Execution (Preserved Interface)
# ---------------------------------------------------------
@st.cache_data(ttl=60)
def load_and_process_civic_data(weather_file: str, traffic_file: str, complaints_file: str):
    """
    Executes the deterministic CityPulse data processing pipeline:
    Normalization -> Rolling Baselines -> Anomaly Detection -> Correlation -> City Pulse
    """
    # 1. Normalization & Schema Validation
    df_unified, val_report = normalize_all_feeds(
        weather_path=weather_file,
        traffic_path=traffic_file,
        complaints_path=complaints_file,
        output_path=None  # Keep in-memory for fast UI reactivity
    )
    
    if df_unified.empty:
        default_city_pulse = {
            "city_pulse_state": "NORMAL",
            "city_pulse_score": 10.0,
            "elevated_zones_count": 0,
            "critical_zones_count": 0,
            "explanation": "No active telemetry feeds available. Baseline city conditions assumed normal.",
            "zone_breakdown": {}
        }
        return df_unified, val_report, pd.DataFrame(), [], default_city_pulse, []
        
    # 2. 15-Minute Rolling Baselines
    df_rolling = compute_rolling_metrics(df_unified, window_minutes=15)
    
    # 3. Rule-Based Anomaly Detection
    df_anomalies = detect_anomalies(df_rolling)
    
    # 4. Multi-Signal Spatial & Temporal Correlation
    correlated_alerts = build_correlation_clusters(df_anomalies, time_window_minutes=20, min_signals=2)
    
    # 5. City & Zone Pulse Status Calculation
    city_pulse, zone_pulses = compute_city_pulse_pipeline(df_anomalies, correlated_alerts)
    
    return df_unified, val_report, df_anomalies, correlated_alerts, city_pulse, zone_pulses

# ---------------------------------------------------------
# Sidebar Controls & Live Simulation Toggles
# ---------------------------------------------------------
st.sidebar.markdown("""<div style="display:flex; align-items:center; gap:10px; margin-bottom:12px;">
<span style="font-size:26px;">🏙️</span>
<span style="font-size:20px; font-weight:800; color:#F8FAFC;">CityPulse V2</span>
</div>""", unsafe_allow_html=True)
st.sidebar.caption(f"Municipal Control Room &bull; **{CITY_NAME}, Rajasthan**")

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Zone Filter")
selected_zone_filter = st.sidebar.selectbox(
    "Focus Municipal Zone:",
    options=["All Zones"] + list(ZONES.keys()),
    index=0
)

st.sidebar.markdown("---")
st.sidebar.subheader("🗺️ Map Engine & Cartography")

has_gmaps_key = bool(get_google_maps_api_key())
map_engine_options = [
    "Auto-Detect (Google Maps if key present)",
    "Google Maps JavaScript API",
    "OpenStreetMap / Folium (Fallback)"
]
map_engine_choice = st.sidebar.selectbox(
    "Cartography Engine:",
    options=map_engine_options,
    index=0,
    help="Google Maps API active" if has_gmaps_key else "Google Maps key not found: defaulting to OSM"
)

if "Google Maps" in map_engine_choice and not map_engine_choice.startswith("Auto"):
    preferred_engine = "google_maps"
elif "OpenStreetMap" in map_engine_choice:
    preferred_engine = "folium"
else:
    preferred_engine = "auto"

map_style = st.sidebar.radio(
    "Tile Style (for OSM Fallback):",
    options=["CartoDB Dark Matter", "CartoDB Positron"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.subheader("🛠️ Feed Resilience Testing")
st.sidebar.caption("Toggle telemetry feeds below to test graceful system degradation:")

enable_weather = st.sidebar.checkbox("Weather Telemetry Active", value=True)
enable_traffic = st.sidebar.checkbox("Traffic Corridors Active", value=True)
enable_complaints = st.sidebar.checkbox("311 Citizen Incidents Active", value=True)

w_path = "data/raw/weather_raw.json" if enable_weather else "data/raw/non_existent.json"
t_path = "data/raw/traffic_raw.csv" if enable_traffic else "data/raw/non_existent.csv"
c_path = "data/raw/complaints_raw.json" if enable_complaints else "data/raw/non_existent.json"

st.sidebar.markdown("---")
st.sidebar.markdown("""<div style="background:rgba(15,23,42,0.8); border:1px solid rgba(255,255,255,0.08); border-radius:8px; padding:12px; font-size:12px; color:#94A3B8;">
<strong style="color:#CBD5E1;">Hackathon Explainability Defense:</strong><br/>
&bull; Zero opaque black-box neural nets.<br/>
&bull; Transparent 15-min rolling baselines.<br/>
&bull; Spatiotemporal correlation window: 20m.<br/>
&bull; Strict non-causation policy enforced.
</div>""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Execute Pipeline
# ---------------------------------------------------------
df_unified, val_report, df_anomalies, alerts, city_pulse, zone_pulses = load_and_process_civic_data(
    w_path, t_path, c_path
)

active_anomalies = get_active_anomalies(df_anomalies)

# Apply zone filter if selected
if selected_zone_filter != "All Zones":
    display_anomalies = active_anomalies[active_anomalies["zone"] == selected_zone_filter]
    display_alerts = [a for a in alerts if a["zone"] == selected_zone_filter]
else:
    display_anomalies = active_anomalies
    display_alerts = alerts

latest_time = df_unified["timestamp"].max().strftime("%H:%M:%S") if not df_unified.empty else "N/A"

# ---------------------------------------------------------
# 1. Polished CityPulse Header
# ---------------------------------------------------------
render_header(city_name=CITY_NAME, latest_sync=latest_time, is_live=True)

# ---------------------------------------------------------
# 10. Clearly Visible Demo Mode Notice
# ---------------------------------------------------------
render_demo_notice()

# ---------------------------------------------------------
# 2. Prominent City Pulse Hero Card
# ---------------------------------------------------------
render_hero_pulse(city_pulse=city_pulse, zone_pulses=zone_pulses)

# ---------------------------------------------------------
# 3. Modern KPI Cards
# ---------------------------------------------------------
render_kpi_cards(df_unified=df_unified, df_anomalies=df_anomalies)

st.markdown("<br/>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 8. Grounded Live Civic Narrative (Phase 13 Engine)
# ---------------------------------------------------------
summary_result = generate_citypulse_summary(
    city_pulse=city_pulse,
    zone_pulses=zone_pulses,
    active_anomalies=active_anomalies,
    correlated_alerts=alerts,
    feed_health=val_report.get("feed_health"),
    use_llm=False  # Instantaneous, grounded deterministic engine
)

render_narrative_card(summary_result=summary_result)

# ---------------------------------------------------------
# 4 & 6. Prominent Map Section + Evidence Explorer
# ---------------------------------------------------------
col_map, col_evidence = st.columns([1.55, 1.45])

with col_map:
    st.subheader(f"🗺️ Live Civic Health Map ({CITY_NAME})")
    render_citypulse_map(
        zone_pulses=zone_pulses,
        anomalies_df=display_anomalies,
        alerts=display_alerts,
        selected_zone=selected_zone_filter,
        map_style=map_style,
        preferred_engine=preferred_engine,
        height=480
    )

with col_evidence:
    # 6. "Why am I seeing this?" Evidence Explorer
    render_evidence_explorer_section(alerts=display_alerts)

st.markdown("<br/>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 5. Dedicated "Active Anomalies" Section
# ---------------------------------------------------------
render_active_anomalies_section(active_anomalies=display_anomalies)

st.markdown("<br/>", unsafe_allow_html=True)

# ---------------------------------------------------------
# Zone-Level Civic Health Grid (6 Zones)
# ---------------------------------------------------------
st.subheader("🏘️ Zone-Level Health Breakdown")
st.caption("Discrete localized health calculations preventing cross-zone panic contagion.")
render_zone_grid(zone_pulses=zone_pulses)

st.markdown("<br/>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 7 & 9. Chronological Timeline & Data Health Monitors
# ---------------------------------------------------------
col_timeline, col_health = st.columns([1.65, 1.35])

with col_timeline:
    st.subheader("⏱️ Chronological Event Timeline")
    st.caption("Verified anomalies with timestamps and calculated baseline deviations.")
    render_timeline(active_anomalies=display_anomalies, limit=10)

with col_health:
    st.subheader("📡 Telemetry Stream Health & Data Pipeline")
    st.caption("Real-time ingestion health and schema normalization validation.")
    render_data_health(val_report=val_report)

# ---------------------------------------------------------
# Footer
# ---------------------------------------------------------
st.markdown("<br/><hr style='border:0; border-top:1px solid rgba(255,255,255,0.08);'/><br/>", unsafe_allow_html=True)
st.markdown("""<div style="text-align:center; font-size:12px; color:#64748B; padding-bottom:20px;">
<strong>CityPulse V2 &bull; AMIHACKS 1.0 Civic Intelligence Platform</strong><br/>
Built by 2nd-Year B.Tech AI & Data Science Students &bull; Fully Explainable Municipal Analytics<br/>
<em>All civic feeds are simulated for hackathon demonstration. Empirical correlations reflect spatiotemporal statistical associations, not verified causation.</em>
</div>""", unsafe_allow_html=True)
