"""
anomaly.py - Rule-Based Anomaly Detection Engine for CityPulse

Implements transparent, explainable detection rules for civic anomalies:
1. RAINFALL_SURGE: Rapid spike in precipitation rate
2. TRAFFIC_SLOWDOWN: Sharp drop in vehicular velocity relative to zone baseline
3. TRANSIT_DELAY_SPIKE: Severe transit queue/delay buildup
4. COMPLAINT_SPIKE: Cluster of urgent citizen complaints in a rolling window

Grounded strictly in data and configurable thresholds (Zero black-box ML for MVP).
"""

import pandas as pd
import numpy as np

# Configurable, defensive rule thresholds
ANOMALY_THRESHOLDS = {
    "rainfall": {
        "surge_min_rate_mm_hr": 20.0,
        "severe_rate_mm_hr": 45.0,
    },
    "traffic_speed": {
        "slowdown_max_speed_kmh": 25.0,
        "critical_speed_kmh": 15.0,
        "min_speed_drop_kmh": -15.0,
    },
    "transit_delay": {
        "delay_min_threshold_min": 15.0,
        "severe_delay_threshold_min": 25.0,
        "min_delay_increase_min": 8.0,
    },
    "complaints": {
        "window_count_threshold": 3,
        "severe_count_threshold": 6,
        "critical_categories": ["waterlogging", "drain_overflow", "traffic_signal_out", "fallen_tree"]
    }
}

def detect_anomalies(df_with_rolling: pd.DataFrame) -> pd.DataFrame:
    """
    Evaluates rule-based anomaly conditions on DataFrame containing rolling metrics.
    
    Returns:
        DataFrame enriched with:
        ['is_anomaly', 'anomaly_type', 'anomaly_severity', 'anomaly_score', 'anomaly_explanation']
    """
    if df_with_rolling.empty:
        return df_with_rolling.copy()
        
    df = df_with_rolling.copy()
    
    is_anomaly = []
    anomaly_type = []
    anomaly_severity = []
    anomaly_score = []
    anomaly_explanation = []
    
    rf_cfg = ANOMALY_THRESHOLDS["rainfall"]
    sp_cfg = ANOMALY_THRESHOLDS["traffic_speed"]
    dl_cfg = ANOMALY_THRESHOLDS["transit_delay"]
    cp_cfg = ANOMALY_THRESHOLDS["complaints"]
    
    for _, row in df.iterrows():
        feed = row["feed_type"]
        val = float(row["value"])
        zone = row["zone"]
        r_mean = float(row.get("rolling_mean", val))
        dev = float(row.get("deviation", 0.0))
        pct = float(row.get("pct_change", 0.0))
        r_count = float(row.get("rolling_count", 1.0))
        etype = str(row.get("event_type", ""))
        
        flag = False
        atype = None
        asev = "NORMAL"
        ascore = 0.0
        aexp = "Normal conditions within baseline tolerance."
        
        # Rule 1: Rainfall Surge
        if feed == "rainfall_rate":
            if val >= rf_cfg["surge_min_rate_mm_hr"]:
                flag = True
                atype = "RAINFALL_SURGE"
                if val >= rf_cfg["severe_rate_mm_hr"]:
                    asev = "HIGH"
                    ascore = 0.95
                else:
                    asev = "MODERATE"
                    ascore = 0.75
                aexp = f"Rainfall rate of {val:.1f} mm/h in {zone} is {pct:+.1f}% above recent baseline ({r_mean:.1f} mm/h)."
                
        # Rule 2: Traffic Slowdown (Sudden drop OR sustained severe gridlock)
        elif feed == "traffic_speed":
            is_sudden_drop = (val <= sp_cfg["slowdown_max_speed_kmh"] and dev <= sp_cfg["min_speed_drop_kmh"])
            is_sustained_gridlock = (val <= sp_cfg["critical_speed_kmh"])
            if is_sudden_drop or is_sustained_gridlock:
                flag = True
                atype = "TRAFFIC_SLOWDOWN"
                if val <= sp_cfg["critical_speed_kmh"]:
                    asev = "HIGH"
                    ascore = 0.90
                else:
                    asev = "MODERATE"
                    ascore = 0.70
                aexp = f"Vehicular speed in {zone} reached {val:.1f} km/h (Normal corridor baseline: 45-55 km/h; deviation: {dev:+.1f} km/h)."
                
        # Rule 3: Transit Delay Spike (Sudden delay jump OR sustained severe delay)
        elif feed == "transit_delay":
            is_sudden_delay = (val >= dl_cfg["delay_min_threshold_min"] and dev >= dl_cfg["min_delay_increase_min"])
            is_sustained_delay = (val >= dl_cfg["severe_delay_threshold_min"])
            if is_sudden_delay or is_sustained_delay:
                flag = True
                atype = "TRANSIT_DELAY_SPIKE"
                if val >= dl_cfg["severe_delay_threshold_min"]:
                    asev = "HIGH"
                    ascore = 0.90
                else:
                    asev = "MODERATE"
                    ascore = 0.70
                aexp = f"Transit delay reached {val:.1f} min in {zone} (Normal baseline: 2-5 min; deviation: {dev:+.1f} min)."
                
        # Rule 4: Citizen Complaint Cluster
        elif feed == "311_incident":
            if r_count >= cp_cfg["window_count_threshold"] and etype in cp_cfg["critical_categories"]:
                flag = True
                atype = "COMPLAINT_SPIKE"
                if r_count >= cp_cfg["severe_count_threshold"]:
                    asev = "HIGH"
                    ascore = 0.90
                else:
                    asev = "MODERATE"
                    ascore = 0.75
                aexp = f"Surge of {int(r_count)} urgent civic complaints in {zone} within 15 minutes ({etype})."
                
        is_anomaly.append(flag)
        anomaly_type.append(atype)
        anomaly_severity.append(asev)
        anomaly_score.append(ascore)
        anomaly_explanation.append(aexp)
        
    df["is_anomaly"] = is_anomaly
    df["anomaly_type"] = anomaly_type
    df["anomaly_severity"] = anomaly_severity
    df["anomaly_score"] = anomaly_score
    df["anomaly_explanation"] = anomaly_explanation
    
    return df

def get_active_anomalies(df_anomalies: pd.DataFrame) -> pd.DataFrame:
    """Filters the DataFrame to return only active anomalous events."""
    if df_anomalies.empty or "is_anomaly" not in df_anomalies.columns:
        return pd.DataFrame()
    return df_anomalies[df_anomalies["is_anomaly"] == True].copy()
