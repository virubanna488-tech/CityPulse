"""
normalize.py - Normalization Layer & Common Data Model Converter

Converts heterogenous civic feeds (Weather JSON, Traffic CSV, 311 Complaints JSON)
into a unified DataFrame conforming to the CityPulse Common Data Model:
- timestamp (pd.Timestamp)
- source (str: 'weather', 'traffic', 'complaints')
- feed_type (str: 'rainfall_rate', 'traffic_speed', 'transit_delay', '311_incident')
- event_type (str: 'precipitation', 'speed_sensor', 'corridor_delay', or complaint type)
- zone (str: 'Zone-A' ... 'Zone-F')
- latitude (float)
- longitude (float)
- value (float)
- unit (str: 'mm/h', 'km/h', 'minutes', 'count')
- severity (str: 'NORMAL', 'LOW', 'MODERATE', 'HIGH')
- confidence (float: 0.0 - 1.0)
"""

import os
import sys
import json
import pandas as pd

# Ensure root directory is on Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.geo_utils import get_zone_coords
from utils.time_utils import parse_timestamp
from utils.validation import validate_dataframe

def normalize_weather_feed(raw_records: list) -> pd.DataFrame:
    """Normalizes raw weather JSON records into the Common Data Model."""
    rows = []
    for item in raw_records:
        ts = parse_timestamp(item.get("recorded_at"))
        zone = item.get("zone_id", "Unknown")
        lat, lon = get_zone_coords(zone)
        precip = float(item.get("rainfall_mm_hr", 0.0))
        
        # Rule-based severity rating for rainfall
        if precip >= 45.0:
            severity = "HIGH"
        elif precip >= 20.0:
            severity = "MODERATE"
        elif precip >= 5.0:
            severity = "LOW"
        else:
            severity = "NORMAL"
            
        rows.append({
            "timestamp": ts,
            "source": "weather",
            "feed_type": "rainfall_rate",
            "event_type": "precipitation",
            "zone": zone,
            "latitude": lat,
            "longitude": lon,
            "value": precip,
            "unit": "mm/h",
            "severity": severity,
            "confidence": 0.95
        })
    return pd.DataFrame(rows)

def normalize_traffic_feed(df_traffic: pd.DataFrame) -> pd.DataFrame:
    """Normalizes raw traffic CSV records into speed and delay records."""
    rows = []
    for _, item in df_traffic.iterrows():
        ts = parse_timestamp(item.get("observation_time"))
        zone = str(item.get("route_zone", "Unknown"))
        lat, lon = get_zone_coords(zone)
        speed = float(item.get("avg_speed_kmh", 0.0))
        delay = float(item.get("delay_minutes", 0.0))
        
        # 1. Traffic Speed Record
        if speed < 15.0:
            speed_sev = "HIGH"
        elif speed < 25.0:
            speed_sev = "MODERATE"
        elif speed < 40.0:
            speed_sev = "LOW"
        else:
            speed_sev = "NORMAL"
            
        rows.append({
            "timestamp": ts,
            "source": "traffic",
            "feed_type": "traffic_speed",
            "event_type": "speed_sensor",
            "zone": zone,
            "latitude": lat,
            "longitude": lon,
            "value": speed,
            "unit": "km/h",
            "severity": speed_sev,
            "confidence": 0.90
        })
        
        # 2. Transit Delay Record
        if delay >= 25.0:
            delay_sev = "HIGH"
        elif delay >= 15.0:
            delay_sev = "MODERATE"
        elif delay >= 8.0:
            delay_sev = "LOW"
        else:
            delay_sev = "NORMAL"
            
        rows.append({
            "timestamp": ts,
            "source": "traffic",
            "feed_type": "transit_delay",
            "event_type": "corridor_delay",
            "zone": zone,
            "latitude": lat,
            "longitude": lon,
            "value": delay,
            "unit": "minutes",
            "severity": delay_sev,
            "confidence": 0.90
        })
    return pd.DataFrame(rows)

def normalize_complaints_feed(raw_records: list) -> pd.DataFrame:
    """Normalizes raw 311 complaints JSON records into the Common Data Model."""
    rows = []
    for item in raw_records:
        ts = parse_timestamp(item.get("created_at"))
        zone = item.get("zone_code", "Unknown")
        lat, lon = get_zone_coords(zone)
        ctype = item.get("complaint_type", "civic_issue")
        
        # High impact categories receive elevated default severity
        if ctype in ["waterlogging", "drain_overflow"]:
            severity = "HIGH"
        elif ctype in ["traffic_signal_out", "fallen_tree"]:
            severity = "MODERATE"
        else:
            severity = "LOW"
            
        rows.append({
            "timestamp": ts,
            "source": "complaints",
            "feed_type": "311_incident",
            "event_type": ctype,
            "zone": zone,
            "latitude": lat,
            "longitude": lon,
            "value": 1.0,
            "unit": "count",
            "severity": severity,
            "confidence": 0.85
        })
    return pd.DataFrame(rows)

def normalize_all_feeds(
    weather_path: str = "data/raw/weather_raw.json",
    traffic_path: str = "data/raw/traffic_raw.csv",
    complaints_path: str = "data/raw/complaints_raw.json",
    output_path: str = "data/processed/unified_civic_data.csv"
) -> tuple[pd.DataFrame, dict]:
    """
    Ingests and normalizes all available feeds into a single unified DataFrame.
    Gracefully handles missing or delayed feeds without throwing fatal crashes.
    """
    frames = []
    feed_health = {
        "weather": "Unavailable",
        "traffic": "Unavailable",
        "complaints": "Unavailable"
    }
    
    # 1. Weather Normalization
    if os.path.exists(weather_path):
        try:
            with open(weather_path, "r", encoding="utf-8") as f:
                w_data = json.load(f)
            df_w = normalize_weather_feed(w_data)
            frames.append(df_w)
            feed_health["weather"] = f"Healthy ({len(df_w)} records)"
        except Exception as e:
            feed_health["weather"] = f"Error: {str(e)}"
            
    # 2. Traffic Normalization
    if os.path.exists(traffic_path):
        try:
            df_t_raw = pd.read_csv(traffic_path)
            df_t = normalize_traffic_feed(df_t_raw)
            frames.append(df_t)
            feed_health["traffic"] = f"Healthy ({len(df_t)} records)"
        except Exception as e:
            feed_health["traffic"] = f"Error: {str(e)}"
            
    # 3. Complaints Normalization
    if os.path.exists(complaints_path):
        try:
            with open(complaints_path, "r", encoding="utf-8") as f:
                c_data = json.load(f)
            df_c = normalize_complaints_feed(c_data)
            frames.append(df_c)
            feed_health["complaints"] = f"Healthy ({len(df_c)} records)"
        except Exception as e:
            feed_health["complaints"] = f"Error: {str(e)}"
            
    if not frames:
        empty_df = pd.DataFrame(columns=[
            "timestamp", "source", "feed_type", "event_type", "zone",
            "latitude", "longitude", "value", "unit", "severity", "confidence"
        ])
        return empty_df, {"error": "No raw feed files were available", "health": feed_health}
        
    # Combine and sort chronologically
    combined = pd.concat(frames, ignore_index=True)
    combined = combined.sort_values(by="timestamp").reset_index(drop=True)
    
    # Run validation and cleanup
    cleaned_df, val_report = validate_dataframe(combined)
    val_report["feed_health"] = feed_health
    
    # Persist processed dataset
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        cleaned_df.to_csv(output_path, index=False)
        
    return cleaned_df, val_report

if __name__ == "__main__":
    df, report = normalize_all_feeds()
    print("====================================================")
    print(">>> NORMALIZATION & COMMON DATA MODEL COMPLETED <<<")
    print("====================================================")
    print(f"Total Normalized Records: {len(df)}")
    print("Feed Status:", report["feed_health"])
    print(f"Validation: {report['initial_rows']} initial -> {report['final_valid_rows']} valid")
    print("\nSample Unified Records:")
    print(df.head(5)[["timestamp", "source", "feed_type", "zone", "value", "unit", "severity"]])
    print("====================================================")
