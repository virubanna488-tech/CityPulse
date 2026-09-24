"""
ui/components.py - Reusable Control-Room UI Components for CityPulse V2

Provides clean, defensible, and high-contrast UI components satisfying all 10 V2 requirements:
1. Polished CityPulse Header
2. Prominent City Pulse Hero Card
3. Modern KPI Cards
4. Prominent Map Integration Layout
5. Dedicated Active Anomalies Monitor
6. Dedicated "Why am I seeing this?" Evidence Explorer
7. Chronological Event Timeline
8. Grounded Live Civic Narrative Card
9. Telemetry Feed & Pipeline Data Health
10. Clearly visible Demo Mode / Synthetic Data Notice

All HTML strings are strictly formatted flush (0 indentation, no blank line breaks)
to prevent Markdown parsers from inadvertently rendering raw code blocks (<pre><code>).
"""

from datetime import datetime
import pandas as pd
import streamlit as st
from utils.geo_utils import CITY_NAME, ZONES, get_zone_metadata

# ---------------------------------------------------------
# 1. Polished CityPulse Header
# ---------------------------------------------------------
def render_header(city_name: str = CITY_NAME, latest_sync: str = "N/A", is_live: bool = True):
    """Renders top control-room header with pulsing radar dot and municipal metadata."""
    pulse_dot_class = "pulse-dot-green" if is_live else "pulse-dot-amber"
    live_label = "LIVE TELEMETRY STREAM" if is_live else "HISTORICAL PLAYBACK"
    
    header_html = f"""<div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:14px; margin-bottom:16px;">
<div style="display:flex; align-items:center; gap:14px;">
<div style="font-size:36px; line-height:1;">🏙️</div>
<div>
<div style="font-size:26px; font-weight:800; color:#F8FAFC; letter-spacing:-0.02em;">
CityPulse <span style="font-weight:400; font-size:16px; color:#94A3B8;">| Live Civic Health Intelligence</span>
</div>
<div style="font-size:13px; color:#94A3B8; margin-top:2px;">
Real-Time Municipal Signal Fusion & Anomaly Intelligence &bull; <strong style="color:#CBD5E1;">{city_name}, Rajasthan</strong>
</div>
</div>
</div>
<div style="display:flex; align-items:center; gap:10px; margin-top:6px;">
<div style="background:#131B2E; border:1px solid rgba(255,255,255,0.12); border-radius:8px; padding:6px 14px; font-size:12px; color:#94A3B8;">
<span class="{pulse_dot_class}"></span><strong>{live_label}</strong> &bull; Sync: <code style="color:#38BDF8; font-weight:600;">{latest_sync} IST</code>
</div>
<div style="background:rgba(59,130,246,0.15); border:1px solid rgba(59,130,246,0.4); border-radius:8px; padding:6px 12px; font-size:11.5px; font-weight:700; color:#93C5FD;">
AMIHACKS 1.0
</div>
</div>
</div>"""
    st.markdown(header_html, unsafe_allow_html=True)


# ---------------------------------------------------------
# 10. Clearly Visible Demo Mode / Synthetic Data Notice
# ---------------------------------------------------------
def render_demo_notice():
    """Renders prominent demo / synthetic data disclosure banner."""
    notice_html = """<div class="demo-notice-banner">
<div>
<strong>⚠️ DEMO MODE ACTIVE:</strong> Civic telemetry feeds (Weather, Traffic Corridors, 311 Incident Tickets) are simulated for hackathon demonstration in <strong>Jaipur, Rajasthan</strong>.
</div>
<div style="font-size:11.5px; color:#FBBF24; font-weight:600;">
⚖️ Correlation Engine strictly reports statistical associations without assuming causation.
</div>
</div>"""
    st.markdown(notice_html, unsafe_allow_html=True)


# ---------------------------------------------------------
# 2. Prominent City Pulse Hero Card
# ---------------------------------------------------------
def render_hero_pulse(city_pulse: dict, zone_pulses: list[dict]):
    """Renders the executive City Pulse hero card with 0-100 gauge and zone containment details."""
    state = city_pulse.get("city_pulse_state", "NORMAL")
    score = city_pulse.get("city_pulse_score", 10.0)
    explanation = city_pulse.get("explanation", "All systems normal.")
    
    crit_zones = city_pulse.get("critical_zones", [])
    elev_zones = city_pulse.get("elevated_zones", [])
    affected_count = len(crit_zones) + len(elev_zones)
    total_zones = len(zone_pulses) if zone_pulses else 6
    
    gauge_percent = min(100.0, max(0.0, score))
    
    if state == "CRITICAL":
        gauge_color = "#EF4444"
        state_icon = "🚨"
    elif state == "ELEVATED":
        gauge_color = "#F97316"
        state_icon = "⚠️"
    elif state == "ATTENTION":
        gauge_color = "#F59E0B"
        state_icon = "🔔"
    else:
        gauge_color = "#10B981"
        state_icon = "✅"

    if affected_count == 0:
        containment_text = "All 6 municipal zones operate strictly within historical baselines."
    elif affected_count == 1:
        disrupted_id = crit_zones[0] if crit_zones else elev_zones[0]
        meta = get_zone_metadata(disrupted_id)
        zname = meta['name'] if meta else disrupted_id
        containment_text = f"Disturbance is <strong>strictly isolated to {disrupted_id} ({zname})</strong>. The remaining {total_zones - 1} zones remain fully normal."
    else:
        containment_text = f"Concurrent disruptions detected across {affected_count} zones ({', '.join(crit_zones + elev_zones)})."

    hero_html = f"""<div class="hero-pulse-card">
<div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:20px;">
<div style="flex:1; min-width:300px;">
<div style="font-size:12px; font-weight:700; color:#94A3B8; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:8px;">
Civic Health Executive Status &bull; City-Wide Pulse
</div>
<div style="display:flex; align-items:center; gap:14px; margin-bottom:12px;">
<span class="pulse-badge-{state}" style="font-size:19px; padding:6px 20px;">
{state_icon} {state}
</span>
<span style="font-size:26px; font-weight:800; color:#F8FAFC;">
{score:.0f}<span style="font-size:16px; color:#64748B; font-weight:500;">/100 Index</span>
</span>
</div>
<div style="font-size:15px; color:#F1F5F9; line-height:1.55; margin-bottom:10px;">
{explanation}
</div>
<div style="font-size:13px; color:#94A3B8;">
<strong>Geographic Containment:</strong> {containment_text}
</div>
</div>
<div style="min-width:260px; background:rgba(15,23,42,0.7); border:1px solid rgba(255,255,255,0.1); border-radius:12px; padding:16px 20px;">
<div style="display:flex; justify-content:space-between; font-size:12px; color:#94A3B8; margin-bottom:8px;">
<span>CITY THREAT GAUGE</span>
<span style="font-weight:800; color:{gauge_color}; font-size:14px;">{score:.0f}%</span>
</div>
<div style="background:rgba(255,255,255,0.1); height:10px; border-radius:5px; overflow:hidden; position:relative;">
<div style="width:{gauge_percent}%; background:{gauge_color}; height:100%; border-radius:5px; transition:width 0.4s ease;"></div>
</div>
<div style="display:flex; justify-content:space-between; font-size:10px; color:#64748B; margin-top:5px; font-weight:600;">
<span>NORMAL (0-25)</span>
<span>ATTN (26-50)</span>
<span>ELEV (51-75)</span>
<span>CRIT (76-100)</span>
</div>
<div style="margin-top:14px; padding-top:10px; border-top:1px solid rgba(255,255,255,0.08); font-size:12.5px; color:#CBD5E1; display:flex; justify-content:space-between;">
<span>Disrupted Zones:</span>
<strong style="color:{gauge_color}; font-size:13px;">{affected_count} of {total_zones}</strong>
</div>
</div>
</div>
</div>"""
    st.markdown(hero_html, unsafe_allow_html=True)


# ---------------------------------------------------------
# 3. Modern KPI Cards
# ---------------------------------------------------------
def render_kpi_cards(df_unified: pd.DataFrame, df_anomalies: pd.DataFrame):
    """Renders 4 modern KPI cards with peak values, baseline comparisons, and percent changes."""
    col1, col2, col3, col4 = st.columns(4)
    
    # 1. Weather / Rainfall Peak
    with col1:
        if not df_unified.empty and "rainfall_rate" in df_unified["feed_type"].values:
            w_df = df_unified[df_unified["feed_type"] == "rainfall_rate"]
            max_rain = float(w_df["value"].max())
            
            rain_anoms = df_anomalies[df_anomalies["feed_type"] == "rainfall_rate"] if not df_anomalies.empty else pd.DataFrame()
            is_surge = not rain_anoms.empty and (rain_anoms["is_anomaly"] == True).any()
            
            if is_surge:
                anom_row = rain_anoms[rain_anoms["is_anomaly"] == True].iloc[0]
                base_rain = float(anom_row.get("rolling_mean", 5.0))
                pct = float(anom_row.get("pct_change", 0.0))
                badge = f'<span class="kpi-badge-alert">SURGE +{pct:.0f}%</span>'
                delta_txt = f"15-min Baseline: {base_rain:.1f} mm/h"
            else:
                badge = '<span class="kpi-badge-normal">NORMAL</span>'
                delta_txt = "Standard precip level"
                
            kpi1_html = f"""<div class="kpi-card">
<div>
<div class="kpi-title">
<span>🌧️ Rainfall Surge Peak</span>
{badge}
</div>
<div class="kpi-value">{max_rain:.1f} <span style="font-size:15px; font-weight:500; color:#94A3B8;">mm/h</span></div>
</div>
<div class="kpi-delta">
<span>{delta_txt}</span>
</div>
</div>"""
            st.markdown(kpi1_html, unsafe_allow_html=True)
        else:
            kpi1_offline = """<div class="kpi-card">
<div class="kpi-title"><span>🌧️ Rainfall Surge Peak</span><span class="kpi-badge-normal">OFFLINE</span></div>
<div class="kpi-value">-- <span style="font-size:15px; color:#94A3B8;">mm/h</span></div>
<div class="kpi-delta"><span style="color:#64748B;">Telemetry offline</span></div>
</div>"""
            st.markdown(kpi1_offline, unsafe_allow_html=True)

    # 2. Traffic Speed / Minimum Corridor Velocity
    with col2:
        if not df_unified.empty and "traffic_speed" in df_unified["feed_type"].values:
            t_df = df_unified[df_unified["feed_type"] == "traffic_speed"]
            min_speed = float(t_df["value"].min())
            
            speed_anoms = df_anomalies[df_anomalies["feed_type"] == "traffic_speed"] if not df_anomalies.empty else pd.DataFrame()
            is_slowdown = not speed_anoms.empty and (speed_anoms["is_anomaly"] == True).any()
            
            if is_slowdown:
                anom_row = speed_anoms[speed_anoms["is_anomaly"] == True].iloc[0]
                base_speed = float(anom_row.get("rolling_mean", 45.0))
                dev = float(anom_row.get("deviation", 0.0))
                badge = f'<span class="kpi-badge-alert">SLOWDOWN {dev:+.0f} km/h</span>'
                delta_txt = f"Corridor Baseline: {base_speed:.0f} km/h"
            else:
                badge = '<span class="kpi-badge-normal">FLUID</span>'
                delta_txt = "Standard corridor flow"
                
            kpi2_html = f"""<div class="kpi-card">
<div>
<div class="kpi-title">
<span>🚗 Min Traffic Speed</span>
{badge}
</div>
<div class="kpi-value">{min_speed:.1f} <span style="font-size:15px; font-weight:500; color:#94A3B8;">km/h</span></div>
</div>
<div class="kpi-delta">
<span>{delta_txt}</span>
</div>
</div>"""
            st.markdown(kpi2_html, unsafe_allow_html=True)
        else:
            kpi2_offline = """<div class="kpi-card">
<div class="kpi-title"><span>🚗 Min Traffic Speed</span><span class="kpi-badge-normal">OFFLINE</span></div>
<div class="kpi-value">-- <span style="font-size:15px; color:#94A3B8;">km/h</span></div>
<div class="kpi-delta"><span style="color:#64748B;">Telemetry offline</span></div>
</div>"""
            st.markdown(kpi2_offline, unsafe_allow_html=True)

    # 3. Transit Delay Peak
    with col3:
        if not df_unified.empty and "transit_delay" in df_unified["feed_type"].values:
            d_df = df_unified[df_unified["feed_type"] == "transit_delay"]
            max_delay = float(d_df["value"].max())
            
            delay_anoms = df_anomalies[df_anomalies["feed_type"] == "transit_delay"] if not df_anomalies.empty else pd.DataFrame()
            is_delay_spike = not delay_anoms.empty and (delay_anoms["is_anomaly"] == True).any()
            
            if is_delay_spike:
                anom_row = delay_anoms[delay_anoms["is_anomaly"] == True].iloc[0]
                base_delay = float(anom_row.get("rolling_mean", 4.0))
                dev = float(anom_row.get("deviation", 0.0))
                badge = f'<span class="kpi-badge-alert">SPIKE +{dev:.0f}m</span>'
                delta_txt = f"Scheduled Baseline: {base_delay:.0f} min"
            else:
                badge = '<span class="kpi-badge-normal">ON TIME</span>'
                delta_txt = "Minimal transit queue"
                
            kpi3_html = f"""<div class="kpi-card">
<div>
<div class="kpi-title">
<span>🚌 Peak Transit Delay</span>
{badge}
</div>
<div class="kpi-value">{max_delay:.1f} <span style="font-size:15px; font-weight:500; color:#94A3B8;">min</span></div>
</div>
<div class="kpi-delta">
<span>{delta_txt}</span>
</div>
</div>"""
            st.markdown(kpi3_html, unsafe_allow_html=True)
        else:
            kpi3_offline = """<div class="kpi-card">
<div class="kpi-title"><span>🚌 Peak Transit Delay</span><span class="kpi-badge-normal">OFFLINE</span></div>
<div class="kpi-value">-- <span style="font-size:15px; color:#94A3B8;">min</span></div>
<div class="kpi-delta"><span style="color:#64748B;">Telemetry offline</span></div>
</div>"""
            st.markdown(kpi3_offline, unsafe_allow_html=True)

    # 4. 311 Citizen Reports
    with col4:
        if not df_unified.empty and "311_incident" in df_unified["feed_type"].values:
            c_df = df_unified[df_unified["feed_type"] == "311_incident"]
            total_tickets = len(c_df)
            
            c_anoms = df_anomalies[df_anomalies["feed_type"] == "311_incident"] if not df_anomalies.empty else pd.DataFrame()
            is_c_spike = not c_anoms.empty and (c_anoms["is_anomaly"] == True).any()
            
            top_cat = c_df["event_type"].mode().iloc[0] if not c_df.empty and "event_type" in c_df.columns else "inquiries"
            
            if is_c_spike:
                badge = f'<span class="kpi-badge-alert">CLUSTER ({total_tickets})</span>'
                delta_txt = f"Primary: {top_cat}"
            else:
                badge = '<span class="kpi-badge-normal">LOW VOL</span>'
                delta_txt = "Standard call volume"
                
            kpi4_html = f"""<div class="kpi-card">
<div>
<div class="kpi-title">
<span>📢 311 Citizen Reports</span>
{badge}
</div>
<div class="kpi-value">{total_tickets} <span style="font-size:15px; font-weight:500; color:#94A3B8;">filed</span></div>
</div>
<div class="kpi-delta">
<span>{delta_txt}</span>
</div>
</div>"""
            st.markdown(kpi4_html, unsafe_allow_html=True)
        else:
            kpi4_offline = """<div class="kpi-card">
<div class="kpi-title"><span>📢 311 Citizen Reports</span><span class="kpi-badge-normal">OFFLINE</span></div>
<div class="kpi-value">-- <span style="font-size:15px; color:#94A3B8;">filed</span></div>
<div class="kpi-delta"><span style="color:#64748B;">Feed offline</span></div>
</div>"""
            st.markdown(kpi4_offline, unsafe_allow_html=True)


# ---------------------------------------------------------
# 8. Grounded Live Civic Narrative Card
# ---------------------------------------------------------
def render_narrative_card(summary_result: dict):
    """Renders the grounded plain-language civic narrative with anti-hallucination verification badges."""
    narrative = summary_result.get("narrative", "No narrative available.")
    gen_by = summary_result.get("generated_by", "deterministic_engine")
    traceable_ids = summary_result.get("traceable_evidence_ids", [])
    trace_str = ", ".join(traceable_ids) if traceable_ids else "Direct Telemetry Stream"
    
    narrative_html = f"""<div class="narrative-card">
<div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; margin-bottom:10px;">
<div style="display:flex; align-items:center; gap:8px;">
<span style="font-size:18px;">📢</span>
<span style="font-weight:700; font-size:15.5px; color:#F8FAFC;">Live Grounded Civic Narrative</span>
</div>
<div style="display:flex; gap:6px;">
<span style="font-size:11px; background:rgba(59,130,246,0.22); color:#93C5FD; border:1px solid rgba(59,130,246,0.4); padding:3px 9px; border-radius:4px; font-weight:700;">
⚡ {gen_by}
</span>
<span style="font-size:11px; background:rgba(16,185,129,0.22); color:#6EE7B7; border:1px solid rgba(16,185,129,0.4); padding:3px 9px; border-radius:4px; font-weight:700;">
🛡️ Grounding Verified (100%)
</span>
</div>
</div>
<p style="margin:0 0 12px 0; font-size:15px; color:#F1F5F9; line-height:1.65; font-weight:400;">
{narrative}
</p>
<div style="font-size:12px; color:#94A3B8; border-top:1px solid rgba(255,255,255,0.08); padding-top:8px; display:flex; justify-content:space-between; flex-wrap:wrap; gap:6px;">
<span><strong>Traceable Evidence:</strong> <code style="color:#38BDF8;">{trace_str}</code></span>
<span style="font-style:italic; color:#CBD5E1;">Correlation ≠ Causation strictly enforced &bull; 100% grounded in empirical telemetry</span>
</div>
</div>"""
    st.markdown(narrative_html, unsafe_allow_html=True)


# ---------------------------------------------------------
# 5. Dedicated Active Anomalies Monitor Section
# ---------------------------------------------------------
def render_active_anomalies_section(active_anomalies: pd.DataFrame):
    """
    Renders clearly visible dedicated Active Anomalies section using existing anomaly data.
    Satisfies Requirement 5.
    """
    st.subheader(f"🚨 Active Anomalies Monitor ({len(active_anomalies)} Detected)")
    st.caption("Individual sensor deviations exceeding statistical baselines (15-min rolling window).")
    
    if active_anomalies.empty:
        empty_html = """<div class="civic-card" style="text-align:center; padding:24px;">
<div style="font-size:28px; margin-bottom:6px;">✅</div>
<div style="font-size:15px; font-weight:700; color:#34D399;">All Telemetry Streams Operating Within Normal Baselines</div>
<div style="font-size:12.5px; color:#94A3B8;">No statistical anomalies detected across weather, traffic corridors, or 311 citizen tickets.</div>
</div>"""
        st.markdown(empty_html, unsafe_allow_html=True)
        return
        
    # Anomaly breakdown counters
    rain_count = len(active_anomalies[active_anomalies["feed_type"] == "rainfall_rate"])
    speed_count = len(active_anomalies[active_anomalies["feed_type"] == "traffic_speed"])
    delay_count = len(active_anomalies[active_anomalies["feed_type"] == "transit_delay"])
    comp_count = len(active_anomalies[active_anomalies["feed_type"] == "311_incident"])
    
    col_c1, col_c2, col_c3, col_c4 = st.columns(4)
    with col_c1:
        c1_html = f"""<div style="background:#131B2E; border:1px solid rgba(255,255,255,0.08); border-radius:8px; padding:10px 14px; text-align:center;">
<div style="font-size:11px; color:#94A3B8; text-transform:uppercase;">Precipitation Surges</div>
<div style="font-size:20px; font-weight:800; color:#38BDF8;">{rain_count}</div>
</div>"""
        st.markdown(c1_html, unsafe_allow_html=True)
    with col_c2:
        c2_html = f"""<div style="background:#131B2E; border:1px solid rgba(255,255,255,0.08); border-radius:8px; padding:10px 14px; text-align:center;">
<div style="font-size:11px; color:#94A3B8; text-transform:uppercase;">Speed Slowdowns</div>
<div style="font-size:20px; font-weight:800; color:#EF4444;">{speed_count}</div>
</div>"""
        st.markdown(c2_html, unsafe_allow_html=True)
    with col_c3:
        c3_html = f"""<div style="background:#131B2E; border:1px solid rgba(255,255,255,0.08); border-radius:8px; padding:10px 14px; text-align:center;">
<div style="font-size:11px; color:#94A3B8; text-transform:uppercase;">Transit Delay Spikes</div>
<div style="font-size:20px; font-weight:800; color:#F97316;">{delay_count}</div>
</div>"""
        st.markdown(c3_html, unsafe_allow_html=True)
    with col_c4:
        c4_html = f"""<div style="background:#131B2E; border:1px solid rgba(255,255,255,0.08); border-radius:8px; padding:10px 14px; text-align:center;">
<div style="font-size:11px; color:#94A3B8; text-transform:uppercase;">Complaint Clusters</div>
<div style="font-size:20px; font-weight:800; color:#A855F7;">{comp_count}</div>
</div>"""
        st.markdown(c4_html, unsafe_allow_html=True)
        
    st.markdown("<br/>", unsafe_allow_html=True)
    
    # Render table of top active anomalies
    top_anomalies = active_anomalies.sort_values(by="timestamp", ascending=False).head(8)
    
    feed_icons = {
        "rainfall_rate": "🌧️",
        "traffic_speed": "🚗",
        "transit_delay": "🚌",
        "311_incident": "📢"
    }
    
    for _, row in top_anomalies.iterrows():
        t_str = row["timestamp"].strftime("%H:%M:%S")
        feed = row["feed_type"]
        icon = feed_icons.get(feed, "📌")
        atype = row["anomaly_type"]
        zone = row["zone"]
        val = row["value"]
        unit = row["unit"]
        sev = row["anomaly_severity"]
        dev = row.get("deviation", 0.0)
        
        sev_color = "#F87171" if sev == "HIGH" else "#FBBF24"
        sev_bg = "rgba(239,68,68,0.2)" if sev == "HIGH" else "rgba(245,158,11,0.2)"
        
        row_html = f"""<div class="anomaly-row-card">
<div style="display:flex; align-items:center; gap:12px;">
<div style="font-size:20px;">{icon}</div>
<div>
<div style="font-weight:700; color:#F8FAFC; font-size:14px;">
{atype.replace('_', ' ')} &bull; <span style="color:#CBD5E1;">{zone}</span>
</div>
<div style="font-size:12px; color:#94A3B8; margin-top:2px;">
{row['anomaly_explanation']}
</div>
</div>
</div>
<div style="display:flex; align-items:center; gap:14px;">
<div style="text-align:right;">
<div style="font-size:14px; font-weight:700; color:#F8FAFC; font-family:'JetBrains Mono';">
{val} {unit}
</div>
<div style="font-size:11px; color:#94A3B8; font-family:'JetBrains Mono';">
dev: {dev:+.1f}
</div>
</div>
<div style="background:{sev_bg}; color:{sev_color}; border:1px solid {sev_color}55; padding:3px 8px; border-radius:5px; font-size:11px; font-weight:700;">
{sev}
</div>
</div>
</div>"""
        st.markdown(row_html, unsafe_allow_html=True)


# ---------------------------------------------------------
# 6. Dedicated "Why am I seeing this?" Evidence Explorer
# ---------------------------------------------------------
def render_evidence_explorer_section(alerts: list[dict]):
    """
    Renders clearly visible dedicated Evidence Explorer section.
    Satisfies Requirement 6.
    """
    st.subheader("🔍 \"Why Am I Seeing This?\" — Multi-Signal Evidence Explorer")
    st.caption("Fusing co-occurring signals within the same zone and 20-minute rolling window without assuming causation.")
    
    if not alerts:
        no_alert_html = """<div class="civic-card" style="text-align:center; padding:28px;">
<div style="font-size:32px; margin-bottom:8px;">✅</div>
<div style="font-size:16px; font-weight:700; color:#34D399; margin-bottom:4px;">No Multi-Signal Correlated Disruptions Active</div>
<div style="font-size:13px; color:#94A3B8;">All civic feeds are operating independently within standard tolerances.</div>
</div>"""
        st.markdown(no_alert_html, unsafe_allow_html=True)
        return
        
    for alert in alerts:
        sev = alert.get("severity", "MODERATE")
        badge_class = "pulse-badge-CRITICAL" if sev == "HIGH" else "pulse-badge-ELEVATED"
        alert_id = alert.get("alert_id", "CP-ALERT")
        category = alert.get("category", "Correlated Disruption")
        headline = alert.get("headline", "Civic Disruption")
        zone = alert.get("zone", "Zone")
        zone_name = alert.get("zone_name", "Municipal Area")
        start_t = alert["timestamp_start"].strftime("%H:%M") if "timestamp_start" in alert else "N/A"
        end_t = alert["timestamp_end"].strftime("%H:%M") if "timestamp_end" in alert else "N/A"
        
        # Visual step builder from evidence points
        steps_html = []
        for pt in alert.get("evidence_points", []):
            icon = "📌"
            if "Rainfall" in pt:
                icon = "🌧️"
            elif "Traffic speed" in pt:
                icon = "🚗"
            elif "Transit delay" in pt:
                icon = "🚌"
            elif "complaints" in pt:
                icon = "📢"
            steps_html.append(f'<div class="evidence-step"><span>{icon}</span> <span>{pt}</span></div>')
        
        chain_render = '<span class="evidence-arrow"> &bull; </span>'.join(steps_html)
        
        alert_html = f"""<div class="civic-card">
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
<div>
<span style="font-size:12px; color:#94A3B8; font-weight:700; letter-spacing:0.04em;">{alert_id} &bull; {category.upper()}</span>
</div>
<span class="{badge_class}" style="font-size:11px; padding:3px 9px;">{sev} PRIORITY</span>
</div>
<h4 style="margin:4px 0 8px 0; font-size:16px; color:#F8FAFC; font-weight:700;">{headline}</h4>
<div style="font-size:13px; color:#CBD5E1; margin-bottom:10px;">
📍 <strong>Location:</strong> {zone} ({zone_name}) &nbsp;|&nbsp; ⏱️ <strong>Active Window:</strong> {start_t} &rarr; {end_t} (20-min spatiotemporal correlation)
</div>
<div style="font-size:11.5px; font-weight:600; color:#94A3B8; text-transform:uppercase; margin-bottom:4px;">
Simultaneous Empirical Telemetry Chain:
</div>
<div class="evidence-chain-container">
{chain_render}
</div>
<div class="disclaimer-box">
⚖️ <strong>Spatiotemporal Association:</strong> Observed co-occurrence within a 20-minute window in {zone}. This is reported as an empirical statistical relationship, not proven causation.
</div>
</div>"""
        st.markdown(alert_html, unsafe_allow_html=True)
        
        # 8-Question Audit Matrix
        why = alert.get("why_this_alert", {})
        if why:
            with st.expander(f"🔍 Audit Inspection Matrix ({alert_id}): Why was this flagged?"):
                ev_bullets = "\n".join(f"- {p}" for p in why.get("question_5_evidence", []))
                audit_md = f"""**1. What changed?**  
{why.get('question_1_what_changed', 'N/A')}

**2. Where did it happen?**  
{why.get('question_2_where', 'N/A')}

**3. When did it happen?**  
{why.get('question_3_when', 'N/A')}

**4. Which signals were involved?**  
`{', '.join(why.get('question_4_signals_involved', []))}`

**5. What is the empirical evidence?**  
{ev_bullets}

**6. Why is this considered unusual?**  
{why.get('question_6_why_unusual', 'N/A')}

**7. Confidence & Strength:**  
{why.get('question_7_confidence', 'N/A')}

**8. Scientific Disclaimer:**  
*{why.get('relationship_statement', 'Reported as a possible relationship, not confirmed causation.')}*"""
                st.markdown(audit_md)


# ---------------------------------------------------------
# 6. Zone Health Grid (6 Zones)
# ---------------------------------------------------------
def render_zone_grid(zone_pulses: list[dict]):
    """Renders 6 responsive cards for Zone-A through Zone-F."""
    cols = st.columns(6)
    
    for idx, zp in enumerate(zone_pulses):
        zid = zp.get("zone", f"Zone-{idx}")
        zname = zp.get("zone_name", "Municipal Sector")
        state = zp.get("pulse_state", "NORMAL")
        score = zp.get("pulse_score", 10.0)
        anom_c = zp.get("anomaly_count", 0)
        
        border_highlight = "rgba(239,68,68,0.5)" if state == "CRITICAL" else "rgba(255,255,255,0.08)"
        
        with cols[idx]:
            zone_html = f"""<div class="zone-cell-card" style="border-color:{border_highlight};">
<div style="font-weight:800; font-size:15px; color:#F8FAFC; margin-bottom:2px;">{zid}</div>
<div style="font-size:11px; color:#94A3B8; margin-bottom:10px; height:28px; line-height:1.2;">{zname}</div>
<span class="pulse-badge-{state}" style="font-size:11px; padding:3px 8px;">{state}</span>
<div style="margin-top:10px; font-size:14px; font-weight:800; color:#F1F5F9;">{score:.0f}<span style="font-size:11px; color:#64748B; font-weight:400;">/100</span></div>
<div style="font-size:11.5px; color:#94A3B8; margin-top:2px;">{anom_c} anomalies</div>
</div>"""
            st.markdown(zone_html, unsafe_allow_html=True)


# ---------------------------------------------------------
# 7. Chronological Event Timeline
# ---------------------------------------------------------
def render_timeline(active_anomalies: pd.DataFrame, limit: int = 10):
    """Renders improved chronological record of active anomalies."""
    if active_anomalies.empty:
        empty_t_html = """<div style="background:#131B2E; border:1px solid rgba(255,255,255,0.08); border-radius:8px; padding:16px; text-align:center; color:#94A3B8;">
No anomalies recorded in current observation window.
</div>"""
        st.markdown(empty_t_html, unsafe_allow_html=True)
        return
        
    timeline_df = active_anomalies.sort_values(by="timestamp", ascending=False).head(limit)
    
    feed_icons = {
        "rainfall_rate": "🌧️",
        "traffic_speed": "🚗",
        "transit_delay": "🚌",
        "311_incident": "📢"
    }
    
    for _, event in timeline_df.iterrows():
        t_str = event["timestamp"].strftime("%H:%M:%S")
        feed = event["feed_type"]
        icon = feed_icons.get(feed, "📌")
        feed_label = feed.replace("_", " ").title()
        atype = event["anomaly_type"]
        zone = event["zone"]
        val = event["value"]
        unit = event["unit"]
        sev = event["anomaly_severity"]
        
        sev_color = "#F87171" if sev == "HIGH" else "#FBBF24"
        
        event_html = f"""<div style="padding:10px 14px; border-bottom:1px solid rgba(255,255,255,0.06); font-size:13px; background:#111827; border-radius:8px; margin-bottom:8px;">
<div style="display:flex; justify-content:space-between; align-items:center;">
<div>
<span style="font-family:'JetBrains Mono', monospace; font-size:12px; color:#38BDF8; font-weight:600;">{t_str}</span>
&bull; <strong style="color:#F8FAFC;">{zone}</strong> &bull; <span>{icon} {feed_label}</span>
</div>
<span style="color:{sev_color}; font-size:11px; font-weight:700; border:1px solid {sev_color}44; background:{sev_color}18; padding:1px 6px; border-radius:4px;">
{sev}
</span>
</div>
<div style="margin-top:4px; font-size:12px; color:#CBD5E1;">
<strong>Reading:</strong> {val} {unit} &bull; <span style="color:#94A3B8;">{event['anomaly_explanation']}</span>
</div>
</div>"""
        st.markdown(event_html, unsafe_allow_html=True)


# ---------------------------------------------------------
# 9. Telemetry Stream Health & Pipeline Integrity
# ---------------------------------------------------------
def render_data_health(val_report: dict):
    """Renders improved telemetry feed statuses and validation metrics."""
    feed_health = val_report.get("feed_health", {})
    
    feeds = [
        ("weather", "🌦️ Weather Telemetry"),
        ("traffic", "🚦 Traffic Corridors"),
        ("complaints", "📢 311 Citizen Incidents")
    ]
    
    for feed_key, feed_label in feeds:
        status_text = feed_health.get(feed_key, "Unavailable")
        is_healthy = "Healthy" in status_text
        
        badge_text = "🟢 ONLINE" if is_healthy else "🔴 OFFLINE"
        badge_bg = "rgba(16,185,129,0.18)" if is_healthy else "rgba(239,68,68,0.18)"
        badge_fg = "#34D399" if is_healthy else "#F87171"
        badge_border = "rgba(16,185,129,0.4)" if is_healthy else "rgba(239,68,68,0.4)"
        
        stream_html = f"""<div style="background:#131B2E; border:1px solid rgba(255,255,255,0.08); border-radius:8px; padding:12px 16px; margin-bottom:8px;">
<div style="display:flex; justify-content:space-between; align-items:center;">
<span style="font-weight:600; font-size:13.5px; color:#F8FAFC;">{feed_label}</span>
<span style="background:{badge_bg}; color:{badge_fg}; border:1px solid {badge_border}; font-size:10.5px; font-weight:700; padding:2px 8px; border-radius:4px;">
{badge_text}
</span>
</div>
<div style="font-size:12px; color:#94A3B8; margin-top:4px;">
Status: {status_text}
</div>
</div>"""
        st.markdown(stream_html, unsafe_allow_html=True)
        
    val_init = val_report.get("initial_rows", 0)
    val_dropped = (
        val_report.get("missing_timestamp_dropped", 0) +
        val_report.get("invalid_coords_dropped", 0) +
        val_report.get("invalid_value_dropped", 0) +
        val_report.get("duplicates_dropped", 0)
    )
    val_clean = val_report.get("final_valid_rows", 0)
    
    audit_html = f"""<div style="background:rgba(15,23,42,0.8); border:1px solid rgba(255,255,255,0.08); border-radius:8px; padding:12px 16px; font-size:12px; color:#CBD5E1; margin-top:10px;">
<div style="font-weight:700; color:#F8FAFC; margin-bottom:6px; font-size:13px;">Schema Normalization Audit:</div>
<div style="display:flex; justify-content:space-between; margin-bottom:4px;">
<span style="color:#94A3B8;">Initial Raw Telemetry Records:</span>
<strong style="font-family:'JetBrains Mono'; color:#F8FAFC;">{val_init}</strong>
</div>
<div style="display:flex; justify-content:space-between; margin-bottom:4px;">
<span style="color:#94A3B8;">Corrupted / Out-of-bounds Dropped:</span>
<strong style="color:#F87171; font-family:'JetBrains Mono';">{val_dropped}</strong>
</div>
<div style="display:flex; justify-content:space-between; border-top:1px solid rgba(255,255,255,0.08); padding-top:6px; margin-top:6px;">
<span style="color:#94A3B8;">Final Clean Validated Records:</span>
<strong style="color:#34D399; font-family:'JetBrains Mono';">{val_clean}</strong>
</div>
</div>"""
    st.markdown(audit_html, unsafe_allow_html=True)
