"""
weather.py - Weather Data Feed Ingestion & Simulation

Generates simulated raw weather station reports across 6 city zones.
Deterministic event: Heavy rainfall begins in Zone-B at 13:25 and peaks at 13:35.
Data is clearly labeled: 'Demo data — simulated civic feeds'.
"""

import json
from datetime import datetime, timedelta
import random

# Fixed random seed to guarantee 100% deterministic demo replay
DEMO_SEED = 42

def generate_weather_raw(start_time: str = "2026-09-24 13:00:00", steps: int = 25, interval_minutes: int = 5):
    """
    Generates raw simulated weather station records.
    Returns a list of raw dictionaries with native weather schema.
    """
    rng = random.Random(DEMO_SEED)
    start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
    
    zones = ["Zone-A", "Zone-B", "Zone-C", "Zone-D", "Zone-E", "Zone-F"]
    records = []
    
    for step in range(steps):
        current_dt = start_dt + timedelta(minutes=step * interval_minutes)
        time_str = current_dt.strftime("%Y-%m-%d %H:%M:%S")
        
        for zone in zones:
            station_id = f"WX-{zone}"
            
            # Baseline normal conditions
            precip = round(rng.uniform(0.0, 1.5), 1)
            temp = round(rng.uniform(28.0, 31.0), 1)
            wind = round(rng.uniform(8.0, 15.0), 1)
            
            # Deterministic scenario: Zone-B experiences heavy storm from 13:25 onwards
            if zone == "Zone-B":
                # Step 5 is 13:25, Step 6 is 13:30, Step 8 is 13:40, etc.
                if step == 5:
                    precip = 18.5  # Rain starting
                elif 6 <= step <= 12:  # 13:30 to 14:00 (Peak storm)
                    precip = round(rng.uniform(55.0, 72.0), 1)
                    wind = round(rng.uniform(35.0, 48.0), 1)
                    temp = 24.5
                elif 13 <= step <= 18: # 14:05 to 14:30 (Easing)
                    precip = round(rng.uniform(15.0, 25.0), 1)
                elif step > 18:        # 14:35 onwards (Light showers)
                    precip = round(rng.uniform(2.0, 6.0), 1)
            
            records.append({
                "station_id": station_id,
                "recorded_at": time_str,
                "zone_id": zone,
                "rainfall_mm_hr": precip,
                "temperature_c": temp,
                "wind_kmh": wind,
                "data_source": "Demo data — simulated civic feeds"
            })
            
    return records

def save_weather_raw(filepath: str = "data/raw/weather_raw.json"):
    """Generates and saves the raw weather observations to a JSON file."""
    data = generate_weather_raw()
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return len(data)

if __name__ == "__main__":
    count = save_weather_raw()
    print(f"Generated {count} raw weather records in data/raw/weather_raw.json")
