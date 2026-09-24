"""
traffic.py - Traffic and Transit Delay Feed Ingestion & Simulation

Generates simulated raw traffic sensor and transit delay records across 6 city zones.
Deterministic event: Heavy congestion and delays develop in Zone-B starting at 13:35 following the rainfall.
Saved as a CSV file to demonstrate multi-format ingestion.
Data is clearly labeled: 'Demo data — simulated civic feeds'.
"""

import csv
from datetime import datetime, timedelta
import random

DEMO_SEED = 42

def generate_traffic_raw(start_time: str = "2026-09-24 13:00:00", steps: int = 25, interval_minutes: int = 5):
    """
    Generates raw simulated traffic corridor records.
    Returns a list of dictionaries with native traffic schema.
    """
    rng = random.Random(DEMO_SEED + 1)
    start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
    
    zones = ["Zone-A", "Zone-B", "Zone-C", "Zone-D", "Zone-E", "Zone-F"]
    records = []
    
    for step in range(steps):
        current_dt = start_dt + timedelta(minutes=step * interval_minutes)
        time_str = current_dt.strftime("%Y-%m-%d %H:%M:%S")
        
        for zone in zones:
            corridor_id = f"TRF-CORR-{zone}"
            
            # Baseline normal conditions
            speed = round(rng.uniform(45.0, 55.0), 1)
            delay = round(rng.uniform(2.0, 5.0), 1)
            congestion = "low"
            
            # Deterministic scenario: Zone-B slows down after rain causes waterlogging
            if zone == "Zone-B":
                # Rain started at step 5 (13:25). By step 7 (13:35) roads start clogging
                if step == 7:
                    speed = 32.0
                    delay = 12.0
                    congestion = "moderate"
                elif 8 <= step <= 13:  # 13:40 to 14:05 (Severe gridlock)
                    speed = round(rng.uniform(10.0, 16.0), 1)
                    delay = round(rng.uniform(26.0, 36.0), 1)
                    congestion = "severe"
                elif 14 <= step <= 18: # 14:10 to 14:30 (Gradual recovery)
                    speed = round(rng.uniform(22.0, 32.0), 1)
                    delay = round(rng.uniform(14.0, 20.0), 1)
                    congestion = "moderate"
                elif step > 18:        # 14:35 onwards (Returning to normal)
                    speed = round(rng.uniform(38.0, 46.0), 1)
                    delay = round(rng.uniform(5.0, 8.0), 1)
                    congestion = "low"
                    
            records.append({
                "corridor_id": corridor_id,
                "observation_time": time_str,
                "route_zone": zone,
                "avg_speed_kmh": speed,
                "delay_minutes": delay,
                "congestion_level": congestion,
                "data_origin": "Demo data — simulated civic feeds"
            })
            
    return records

def save_traffic_raw(filepath: str = "data/raw/traffic_raw.csv"):
    """Generates and saves the raw traffic observations to a CSV file."""
    data = generate_traffic_raw()
    fieldnames = ["corridor_id", "observation_time", "route_zone", "avg_speed_kmh", "delay_minutes", "congestion_level", "data_origin"]
    
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
        
    return len(data)

if __name__ == "__main__":
    count = save_traffic_raw()
    print(f"Generated {count} raw traffic records in data/raw/traffic_raw.csv")
