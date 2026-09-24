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

# ---------------------------------------------------------
# Page Configuration & Clean Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="CityPulse — Live Civic Health Dashboard",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for high-contrast civic dashboard cards
st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 14px 18px;
        border: 1px solid #e9ecef;
        margin-bottom: 10px;
    }
    .pulse-badge-CRITICAL {
        background-color: #dc3545;
        color: white;
        padding: 6px 14px;
        border-radius: 6px;
        font-weight: 700;
        display: inline-block;
    }
    .pulse-badge-ELEVATED {
        background-color: #fd7e14;
        color: white;
        padding: 6px 14px;
        border-radius: 6px;
        font-weight: 700;
        display: inline-block;
    }
    .pulse-badge-ATTENTION {
        background-color: #ffc107;
        color: #212529;
        padding: 6px 14px;
        border-radius: 6px;
        font-weight: 700;
        display: inline-block;
    }
    .pulse-badge-NORMAL {
        background-color: #28a745;
        color: white;
        padding: 6px 14px;
        border-radius: 6px;
        font-weight: 700;
        display: inline-block;
    }
    .evidence-box {
        background-color: #fff3cd;
        border-left: 5px solid #ffc107;
        padding: 12px 16px;
        border-radius: 4px;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Data Pipeline Caching / Execution
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
st.sidebar.title("🏙️ CityPulse Controls")
st.sidebar.caption(f"Municipal Monitoring System — **{CITY_NAME}**")

st.sidebar.markdown("---")
st.sidebar.subheader("🛠️ Feed Resilience Testing")
st.sidebar.info("Toggle feeds below to test how CityPulse gracefully degrades during API outages.")

# Toggles for testing missing feeds
enable_weather = st.sidebar.checkbox("Weather Feed Active", value=True)
enable_traffic = st.sidebar.checkbox("Traffic Feed Active", value=True)
enable_complaints = st.sidebar.checkbox("311 Complaints Active", value=True)

w_path = "data/raw/weather_raw.json" if enable_weather else "data/raw/non_existent.json"
t_path = "data/raw/traffic_raw.csv" if enable_traffic else "data/raw/non_existent.csv"
c_path = "data/raw/complaints_raw.json" if enable_complaints else "data/raw/non_existent.json"

st.sidebar.markdown("---")
selected_zone_filter = st.sidebar.selectbox(
    "Filter by Zone:",
    options=["All Zones"] + list(ZONES.keys()),
    index=0
)

st.sidebar.markdown("---")
st.sidebar.markdown("""
**Data Integrity Notice**:
All data shown is clearly labeled:
`Demo data — simulated civic feeds`
Created for AMIHACKS 1.0 demonstration.
""")

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

# ---------------------------------------------------------
# 1. Header & Live Pulse Status (10-Second Understanding)
# ---------------------------------------------------------
st.title("CityPulse — The Live Civic Health Dashboard")
st.caption(f"Real-time multi-signal civic health monitoring for **{CITY_NAME}, Rajasthan**")

pulse_state = city_pulse.get("city_pulse_state", "NORMAL")
pulse_score = city_pulse.get("city_pulse_score", 10.0)

# Main Banner
col_pulse, col_m1, col_m2, col_m3, col_m4 = st.columns([2.5, 1, 1, 1, 1.2])

with col_pulse:
    st.markdown(f"""
    <div style="background:#f1f3f5; padding:16px 20px; border-radius:10px; border-left:6px solid #495057;">
        <span style="font-size:14px; text-transform:uppercase; color:#6c757d; font-weight:600;">Overall City Status</span>
        <div style="margin-top:6px;">
            <span class="pulse-badge-{pulse_state}" style="font-size:20px;">{pulse_state}</span>
            <span style="font-size:18px; margin-left:12px; font-weight:600; color:#343a40;">Index: {pulse_score:.0f}/100</span>
        </div>
        <p style="margin-top:8px; margin-bottom:0; font-size:13.5px; color:#495057;">{city_pulse.get('explanation', '')}</p>
    </div>
    """, unsafe_allow_html=True)

with col_m1:
    st.metric("Active Anomalies", len(active_anomalies))
with col_m2:
    crit_count = len(city_pulse.get("critical_zones", [])) + len(city_pulse.get("elevated_zones", []))
    st.metric("Disrupted Zones", f"{crit_count}/6")
with col_m3:
    st.metric("Correlated Alerts", len(alerts))
with col_m4:
    latest_time = df_unified["timestamp"].max().strftime("%H:%M:%S") if not df_unified.empty else "N/A"
    st.metric("Latest Sync", latest_time)

st.markdown("<br/>", unsafe_allow_html=True)

# ---------------------------------------------------------
# Grounded Plain-Language Civic Summary (Phase 13)
# ---------------------------------------------------------
summary_result = generate_citypulse_summary(
    city_pulse=city_pulse,
    zone_pulses=zone_pulses,
    active_anomalies=active_anomalies,
    correlated_alerts=alerts,
    feed_health=val_report.get("feed_health"),
    use_llm=False  # Instantaneous, grounded deterministic engine
)

st.markdown(f"""
<div style="background:#eef2f7; border-left: 5px solid #0d6efd; padding: 14px 18px; border-radius: 6px; margin-bottom: 20px;">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 6px;">
        <span style="font-weight:700; font-size:15px; color:#1a252f;">📢 Live Grounded Civic Narrative</span>
        <span style="font-size:11px; background:#d0e2ff; color:#084298; padding:3px 8px; border-radius:4px; font-weight:600;">⚡ {summary_result['generated_by']}</span>
    </div>
    <p style="margin:0; font-size:14px; color:#2c3e50; line-height:1.5;">
        {summary_result['narrative']}
    </p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 2. Main Body: Interactive Map + Active Correlated Alert
# ---------------------------------------------------------
col_map, col_alert = st.columns([1.6, 1.4])

with col_map:
    st.subheader(f"🗺️ Live Civic Health Map ({CITY_NAME})")
    st.caption("Interactive OpenStreetMap with zone health rings and active multi-feed anomalies.")
    
    # Initialize Folium Map
    m = folium.Map(
        location=[CITY_CENTER["latitude"], CITY_CENTER["longitude"]],
        zoom_start=CITY_CENTER["zoom_start"],
        tiles="CartoDB positron"
    )
    
    # 1. Plot Zone Polygons / Circles
    zone_color_map = {
        "NORMAL": "#28a745",
        "ATTENTION": "#ffc107",
        "ELEVATED": "#fd7e14",
        "CRITICAL": "#dc3545"
    }
    
    for zp in zone_pulses:
        zid = zp["zone"]
        zmeta = get_zone_metadata(zid)
        color = zone_color_map.get(zp["pulse_state"], "#6c757d")
        
        # Zone Health Ring
        folium.Circle(
            location=[zmeta["latitude"], zmeta["longitude"]],
            radius=1500,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.18,
            weight=2,
            tooltip=f"{zid} ({zmeta['name']}): {zp['pulse_state']} ({zp['anomaly_count']} anomalies)",
            popup=folium.Popup(f"""
            <b>{zid}: {zmeta['name']}</b><br/>
            Status: <b>{zp['pulse_state']}</b> (Score: {zp['pulse_score']}/100)<br/>
            {zp['explanation']}
            """, max_width=300)
        ).add_to(m)
        
    # 2. Plot Active Anomalies on Map
    feed_icon_colors = {
        "rainfall_rate": "blue",
        "traffic_speed": "red",
        "transit_delay": "orange",
        "311_incident": "purple"
    }
    
    for _, anom in display_anomalies.iterrows():
        lat = anom["latitude"]
        lon = anom["longitude"]
        feed = anom["feed_type"]
        atype = anom["anomaly_type"]
        val = anom["value"]
        unit = anom["unit"]
        sev = anom["anomaly_severity"]
        
        icon_color = feed_icon_colors.get(feed, "gray")
        
        folium.CircleMarker(
            location=[lat, lon],
            radius=7,
            color=icon_color,
            fill=True,
            fill_color=icon_color,
            fill_opacity=0.85,
            popup=folium.Popup(f"""
            <b>{atype}</b> ({sev})<br/>
            Zone: {anom['zone']}<br/>
            Reading: <b>{val} {unit}</b><br/>
            Time: {anom['timestamp'].strftime('%H:%M:%S')}<br/>
            <i>{anom['anomaly_explanation']}</i>
            """, max_width=280)
        ).add_to(m)
        
    st_folium(m, height=440, use_container_width=True, returned_objects=[])

with col_alert:
    st.subheader("🚨 Priority Multi-Signal Alerts")
    st.caption("Fusing co-occurring signals within the same zone and 20-minute window.")
    
    if not display_alerts:
        st.success("✅ **No active multi-signal correlated disruptions.** All civic signals are independent and within baseline limits.")
    else:
        for idx, alert in enumerate(display_alerts):
            sev = alert["severity"]
            badge_color = "#dc3545" if sev == "HIGH" else "#fd7e14"
            
            with st.container():
                st.markdown(f"""
                <div style="border: 1px solid #ced4da; border-radius: 8px; padding: 14px; margin-bottom: 12px; background: white;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-size:12px; color:#6c757d; font-weight:600;">{alert['alert_id']} &bull; {alert['category']}</span>
                        <span style="background:{badge_color}; color:white; padding:3px 8px; border-radius:4px; font-size:11px; font-weight:bold;">{sev} SEVERITY</span>
                    </div>
                    <h4 style="margin: 8px 0; font-size: 16px; color:#212529;">{alert['headline']}</h4>
                    <p style="font-size:13px; color:#495057; margin-bottom: 8px;">
                        <b>Location:</b> {alert['zone']} ({alert['zone_name']})<br/>
                        <b>Active Window:</b> {alert['timestamp_start'].strftime('%H:%M')} &rarr; {alert['timestamp_end'].strftime('%H:%M')}
                    </p>
                    <div style="background:#f8f9fa; border-radius:6px; padding:8px 12px; font-size:12.5px;">
                        <b>Calculated Empirical Evidence:</b>
                        <ul style="margin:4px 0 0 0; padding-left:18px;">
                            {''.join(f'<li>{p}</li>' for p in alert['evidence_points'])}
                        </ul>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # 'WHY THIS ALERT?' Inspection Expander
                why = alert["why_this_alert"]
                with st.expander(f"🔍 WHY THIS ALERT? (Audit {alert['alert_id']})"):
                    st.markdown(f"""
                    **1. What changed?**  
                    {why['question_1_what_changed']}
                    
                    **2. Where did it happen?**  
                    {why['question_2_where']}
                    
                    **3. When did it happen?**  
                    {why['question_3_when']}
                    
                    **4. Which signals were involved?**  
                    {', '.join(why['question_4_signals_involved'])}
                    
                    **5. What is the evidence?**  
                    * {'<br/>* '.join(why['question_5_evidence'])}
                    
                    **6. Why is this considered unusual?**  
                    {why['question_6_why_unusual']}
                    
                    **7. Confidence & Strength:**  
                    {why['question_7_confidence']}
                    
                    **8. Scientific Disclaimer:**  
                    *{why['relationship_statement']}*
                    """)

st.markdown("---")

# ---------------------------------------------------------
# 3. Zone Health Grid
# ---------------------------------------------------------
st.subheader("🏘️ Zone-Level Health Breakdown")
z_cols = st.columns(6)

for i, zp in enumerate(zone_pulses):
    zid = zp["zone"]
    state = zp["pulse_state"]
    score = zp["pulse_score"]
    anom_c = zp["anomaly_count"]
    
    with z_cols[i]:
        st.markdown(f"""
        <div class="metric-card" style="text-align:center;">
            <div style="font-weight:700; font-size:14px; margin-bottom:4px;">{zid}</div>
            <div style="font-size:11px; color:#6c757d; margin-bottom:8px; height:28px;">{zp['zone_name']}</div>
            <span class="pulse-badge-{state}" style="font-size:12px; padding:3px 8px;">{state}</span>
            <div style="margin-top:8px; font-size:12px; color:#495057;">Score: <b>{score:.0f}</b>/100</div>
            <div style="font-size:11px; color:#6c757d;">{anom_c} anomalies</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# ---------------------------------------------------------
# 4. Event Timeline & Data Health
# ---------------------------------------------------------
col_timeline, col_health = st.columns([1.7, 1.3])

with col_timeline:
    st.subheader("⏱️ Recent Event Timeline")
    st.caption("Chronological record of verified anomalies and alert milestones.")
    
    if active_anomalies.empty:
        st.info("No anomalies detected in the current observation window.")
    else:
        # Show top 12 most recent events chronologically
        timeline_df = active_anomalies.sort_values(by="timestamp", ascending=False).head(12)
        
        for _, event in timeline_df.iterrows():
            t_str = event["timestamp"].strftime("%H:%M:%S")
            feed = event["feed_type"].replace("_", " ").title()
            atype = event["anomaly_type"]
            zone = event["zone"]
            val = event["value"]
            unit = event["unit"]
            sev = event["anomaly_severity"]
            badge = "🔴" if sev == "HIGH" else "🟡"
            
            st.markdown(f"""
            <div style="padding:8px 12px; border-bottom:1px solid #e9ecef; font-size:13px;">
                <b>{t_str}</b> &bull; {badge} <b>{zone}</b> &bull; <code>{feed}</code>: {atype}<br/>
                <span style="color:#6c757d; font-size:12px;">Reading: {val} {unit} &bull; {event['anomaly_explanation']}</span>
            </div>
            """, unsafe_allow_html=True)

with col_health:
    st.subheader("📡 Feed Health & System Integrity")
    st.caption("Status of active municipal data streams and data-normalization health.")
    
    feed_health = val_report.get("feed_health", {})
    
    for feed_name, icon in [("weather", "🌦️ Weather Telemetry"), ("traffic", "🚦 Traffic Corridors"), ("complaints", "📢 311 Incident Tickets")]:
        status_text = feed_health.get(feed_name, "Unavailable")
        is_healthy = "Healthy" in status_text
        
        status_badge = "🟢 ONLINE" if is_healthy else "🔴 OFFLINE"
        badge_bg = "#d4edda" if is_healthy else "#f8d7da"
        badge_fg = "#155724" if is_healthy else "#721c24"
        
        st.markdown(f"""
        <div style="background:#ffffff; border:1px solid #dee2e6; border-radius:6px; padding:10px 14px; margin-bottom:10px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-weight:600; font-size:13.5px;">{icon}</span>
                <span style="background:{badge_bg}; color:{badge_fg}; font-size:11px; font-weight:700; padding:2px 8px; border-radius:4px;">{status_badge}</span>
            </div>
            <div style="font-size:12px; color:#6c757d; margin-top:4px;">
                Status: {status_text}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("""
    <div style="background:#e9ecef; border-radius:6px; padding:10px 12px; font-size:12px; color:#495057; margin-top:12px;">
        <b>Validation Integrity:</b><br/>
        &bull; Initial Ingested Rows: {val_init}<br/>
        &bull; Malformed / Null Rows Dropped: {val_dropped}<br/>
        &bull; Valid Clean Records: {val_clean}
    </div>
    """.format(
        val_init=val_report.get("initial_rows", 0),
        val_dropped=val_report.get("missing_timestamp_dropped", 0) + val_report.get("invalid_coords_dropped", 0) + val_report.get("invalid_value_dropped", 0) + val_report.get("duplicates_dropped", 0),
        val_clean=val_report.get("final_valid_rows", 0)
    ), unsafe_allow_html=True)

# ---------------------------------------------------------
# Footer
# ---------------------------------------------------------
st.markdown("---")
st.markdown("""
<div style="text-align:center; font-size:12px; color:#6c757d;">
    <b>CityPulse MVP &bull; AMIHACKS 1.0</b> &bull; Built with Python, Pandas, Streamlit & OpenStreetMap.<br/>
    <i>Empowering municipal decision makers with explainable civic signal fusion.</i>
</div>
""", unsafe_allow_html=True)
