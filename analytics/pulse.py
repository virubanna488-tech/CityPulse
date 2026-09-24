"""
pulse.py - City Pulse Overall Status & Scoring Engine for CityPulse

Calculates explainable health indices and categorical pulse states:
NORMAL, ATTENTION, ELEVATED, CRITICAL.

Key Design Principles:
1. Complete transparency: No black-box ML or arbitrary magic numbers.
2. Zone isolation: Severe distress in one localized zone raises that zone to CRITICAL,
   while keeping the City-Wide pulse at ELEVATED (preventing panic across unaffected areas).
3. Full traceability: Every pulse state reports the exact contributing anomalies and signals.
"""

import os
import sys
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Ensure root directory is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.geo_utils import get_zone_list, get_zone_metadata

# Configurable score bounds and classification thresholds
PULSE_THRESHOLDS = {
    "NORMAL": (0, 25),
    "ATTENTION": (26, 50),
    "ELEVATED": (51, 75),
    "CRITICAL": (76, 100)
}

def score_to_pulse_state(score: float) -> str:
    """Maps a numerical score (0-100) to its categorical pulse state."""
    if score >= 76.0:
        return "CRITICAL"
    elif score >= 51.0:
        return "ELEVATED"
    elif score >= 26.0:
        return "ATTENTION"
    else:
        return "NORMAL"

def calculate_zone_pulse(
    zone_id: str,
    active_anomalies_df: pd.DataFrame,
    has_correlated_alert: bool = False
) -> dict:
    """
    Computes the transparent pulse status for an individual zone.
    
    Calculation Rules:
    - Base score: 10 (normal civic baseline)
    - +15 points per MODERATE anomaly
    - +25 points per HIGH anomaly
    - +20 bonus if multiple distinct feeds are anomalous simultaneously
    - +20 bonus if multi-signal correlated alert is active in this zone
    - Capped at 100.
    """
    zone_meta = get_zone_metadata(zone_id) or {"name": zone_id, "description": "Civic Zone"}
    
    # Filter anomalies belonging to this zone
    if active_anomalies_df.empty or "zone" not in active_anomalies_df.columns:
        zone_anoms = pd.DataFrame()
    else:
        zone_anoms = active_anomalies_df[active_anomalies_df["zone"] == zone_id].copy()
        
    anomaly_count = len(zone_anoms)
    unique_feeds = list(zone_anoms["feed_type"].unique()) if anomaly_count > 0 else []
    
    score = 10.0  # Base healthy city score
    contributing_factors = []
    
    if anomaly_count > 0:
        mod_count = (zone_anoms["anomaly_severity"] == "MODERATE").sum()
        high_count = (zone_anoms["anomaly_severity"] == "HIGH").sum()
        
        score += (mod_count * 15.0)
        score += (high_count * 25.0)
        
        if mod_count > 0:
            contributing_factors.append(f"{mod_count} moderate anomal{'y' if mod_count == 1 else 'ies'}")
        if high_count > 0:
            contributing_factors.append(f"{high_count} high-severity anomal{'y' if high_count == 1 else 'ies'}")
            
        # Multi-feed synergy bonus
        if len(unique_feeds) >= 2:
            score += 20.0
            contributing_factors.append(f"Multi-feed impact across {len(unique_feeds)} distinct data channels")
            
        # Correlated incident bonus
        if has_correlated_alert:
            score += 20.0
            contributing_factors.append("Active multi-signal correlated disruption alert")
            
    score = float(min(100.0, score))
    pulse_state = score_to_pulse_state(score)
    
    # Generate human-readable explanation
    if pulse_state == "NORMAL":
        explanation = f"{zone_id} ({zone_meta['name']}) is operating within normal baseline parameters. No active anomalies."
    elif pulse_state == "ATTENTION":
        feed_names = ", ".join(f.replace("_", " ").title() for f in unique_feeds)
        explanation = f"{zone_id} ({zone_meta['name']}) under ATTENTION due to unusual activity in {feed_names}."
    elif pulse_state == "ELEVATED":
        feed_names = ", ".join(f.replace("_", " ").title() for f in unique_feeds)
        explanation = f"{zone_id} ({zone_meta['name']}) ELEVATED due to significant disruption across {feed_names}."
    else: # CRITICAL
        feed_names = ", ".join(f.replace("_", " ").title() for f in unique_feeds)
        explanation = f"CRITICAL alert in {zone_id} ({zone_meta['name']}). Severe compound disruption involving {feed_names}."
        
    return {
        "zone": zone_id,
        "zone_name": zone_meta["name"],
        "pulse_state": pulse_state,
        "pulse_score": score,
        "anomaly_count": anomaly_count,
        "unique_feeds": unique_feeds,
        "contributing_factors": contributing_factors,
        "explanation": explanation
    }

def calculate_city_pulse(
    zone_pulses: list[dict],
    correlated_alerts: list[dict] = None
) -> dict:
    """
    Computes overall City-Wide Pulse by aggregating individual zone health.
    
    Aggregation Rules:
    - Average score of all zones provides the numeric baseline.
    - City Pulse State logic:
      * CRITICAL: >= 2 zones in CRITICAL, OR >= 3 zones in ELEVATED.
      * ELEVATED: 1 zone in CRITICAL, OR >= 2 zones in ELEVATED.
      * ATTENTION: 1 zone in ELEVATED, OR >= 2 zones in ATTENTION.
      * NORMAL: All zones NORMAL (or at most 1 in ATTENTION).
    """
    if not zone_pulses:
        return {
            "city_pulse_state": "NORMAL",
            "city_pulse_score": 10.0,
            "elevated_zones_count": 0,
            "critical_zones_count": 0,
            "explanation": "No active telemetry. Baseline city conditions assumed normal.",
            "zone_breakdown": {}
        }
        
    scores = [z["pulse_score"] for z in zone_pulses]
    avg_score = float(np.mean(scores))
    
    crit_zones = [z["zone"] for z in zone_pulses if z["pulse_state"] == "CRITICAL"]
    elev_zones = [z["zone"] for z in zone_pulses if z["pulse_state"] == "ELEVATED"]
    attn_zones = [z["zone"] for z in zone_pulses if z["pulse_state"] == "ATTENTION"]
    
    num_crit = len(crit_zones)
    num_elev = len(elev_zones)
    num_attn = len(attn_zones)
    
    # Determine city-wide pulse state
    if num_crit >= 2 or num_elev >= 3:
        city_state = "CRITICAL"
        city_score = max(80.0, avg_score * 1.5)
        explanation = f"City Pulse is CRITICAL: Multiple zones ({', '.join(crit_zones + elev_zones)}) experiencing severe simultaneous disruptions."
    elif num_crit == 1 or num_elev >= 2:
        city_state = "ELEVATED"
        city_score = max(55.0, avg_score * 1.3)
        if num_crit == 1:
            explanation = f"City Pulse is ELEVATED: Severe localized disruption active in {crit_zones[0]}, while remaining {len(zone_pulses) - 1} zones remain largely stable."
        else:
            explanation = f"City Pulse is ELEVATED: Concurrent disruptions detected across {', '.join(elev_zones)}."
    elif num_elev == 1 or num_attn >= 2:
        city_state = "ATTENTION"
        city_score = max(35.0, avg_score * 1.1)
        explanation = f"City Pulse is ATTENTION: Mild unusual activity requiring monitoring in {', '.join(elev_zones + attn_zones)}."
    else:
        city_state = "NORMAL"
        city_score = min(25.0, avg_score)
        explanation = "City Pulse is NORMAL: All civic systems functioning within standard tolerances."
        
    city_score = float(min(100.0, round(city_score, 1)))
    
    return {
        "city_pulse_state": city_state,
        "city_pulse_score": city_score,
        "average_zone_score": round(avg_score, 1),
        "critical_zones": crit_zones,
        "elevated_zones": elev_zones,
        "attention_zones": attn_zones,
        "explanation": explanation,
        "zone_breakdown": {z["zone"]: z for z in zone_pulses}
    }

def compute_city_pulse_pipeline(
    df_anomalies: pd.DataFrame,
    correlated_alerts: list[dict] = None
) -> tuple[dict, list[dict]]:
    """
    Master function: Computes zone-level and city-wide pulse from anomaly outputs.
    """
    zones = get_zone_list()
    active_anomalies = df_anomalies[df_anomalies["is_anomaly"] == True] if not df_anomalies.empty and "is_anomaly" in df_anomalies.columns else pd.DataFrame()
    
    # Determine which zones have active correlated alerts
    alert_zones = set()
    if correlated_alerts:
        alert_zones = {a["zone"] for a in correlated_alerts}
        
    zone_pulses = []
    for z in zones:
        has_alert = z in alert_zones
        z_pulse = calculate_zone_pulse(z, active_anomalies, has_correlated_alert=has_alert)
        zone_pulses.append(z_pulse)
        
    city_pulse = calculate_city_pulse(zone_pulses, correlated_alerts)
    return city_pulse, zone_pulses

if __name__ == "__main__":
    from analytics.rolling import compute_rolling_metrics
    from analytics.anomaly import detect_anomalies
    from correlation.correlation_engine import build_correlation_clusters
    
    df_raw = pd.read_csv("data/processed/unified_civic_data.csv")
    df_roll = compute_rolling_metrics(df_raw, window_minutes=15)
    df_anom = detect_anomalies(df_roll)
    alerts = build_correlation_clusters(df_anom, time_window_minutes=20)
    
    city_pulse, zone_pulses = compute_city_pulse_pipeline(df_anom, alerts)
    
    print("====================================================")
    print(">>> CITYPULSE STATUS & SCORING RESULTS <<<")
    print("====================================================")
    print(f"Overall City Pulse State: {city_pulse['city_pulse_state']} (Score: {city_pulse['city_pulse_score']}/100)")
    print(f"Explanation: {city_pulse['explanation']}")
    print("\nZone-by-Zone Status:")
    for zp in zone_pulses:
        print(f"  * {zp['zone']} ({zp['zone_name']}): {zp['pulse_state']} (Score: {zp['pulse_score']}) | {zp['anomaly_count']} anomalies")
    print("====================================================")
