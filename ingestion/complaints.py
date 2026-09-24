"""
complaints.py - 311 Citizen Complaints Feed Ingestion & Simulation

Generates simulated raw 311 civic complaint tickets across 6 city zones.
Deterministic event: Sharp spike in 'waterlogging' and 'drain_overflow' complaints in Zone-B starting at 13:30.
Privacy: Contains zero PII (personally identifiable information) - only anonymous ticket IDs and incident types.
Data is clearly labeled: 'Demo data — simulated civic feeds'.
"""

import json
from datetime import datetime, timedelta
import random

DEMO_SEED = 42

def generate_complaints_raw(start_time: str = "2026-09-24 13:00:00", duration_minutes: int = 120):
    """
    Generates event-based raw 311 complaints.
    Returns a list of raw complaint tickets.
    """
    rng = random.Random(DEMO_SEED + 2)
    start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
    
    zones = ["Zone-A", "Zone-B", "Zone-C", "Zone-D", "Zone-E", "Zone-F"]
    tickets = []
    ticket_counter = 1000
    
    # 1. Background civic complaints across all zones (routine city noise/lights/potholes)
    routine_types = [
        ("pothole", "Pothole reported on secondary road"),
        ("streetlight_fault", "Streetlight blinking or inactive"),
        ("noise_complaint", "Loud construction past allowed hours"),
        ("garbage_overflow", "Public bin needs clearing")
    ]
    
    for minute in range(0, duration_minutes, 8):
        current_dt = start_dt + timedelta(minutes=minute, seconds=rng.randint(0, 59))
        time_str = current_dt.strftime("%Y-%m-%d %H:%M:%S")
        
        # Pick 1 random zone occasionally
        if rng.random() < 0.6:
            zone = rng.choice(zones)
            ctype, desc = rng.choice(routine_types)
            ticket_counter += 1
            tickets.append({
                "ticket_id": f"TKT-{ticket_counter}",
                "created_at": time_str,
                "zone_code": zone,
                "complaint_type": ctype,
                "description": desc,
                "source_system": "Demo data — simulated civic feeds"
            })
            
    # 2. Deterministic incident surge: Waterlogging & Drainage in Zone-B
    # Surge schedule: (start_minute, end_minute, count, types)
    surge_windows = [
        (30, 35, 3, [("waterlogging", "Water accumulation near market junction")]),
        (35, 45, 8, [("waterlogging", "Waterlogging knee-deep on main transit artery"),
                     ("drain_overflow", "Storm drain clogged and overflowing onto road")]),
        (45, 60, 10, [("waterlogging", "Vehicles stranded due to street flooding"),
                      ("drain_overflow", "Drainage backing up near bus stop"),
                      ("traffic_signal_out", "Water ingress caused signal outage")]),
        (60, 75, 5, [("waterlogging", "Receding slowly, drainage still partially blocked")]),
        (75, 90, 2, [("waterlogging", "Pavement standing water clearing")])
    ]
    
    for start_min, end_min, count, type_pool in surge_windows:
        for _ in range(count):
            offset_sec = rng.randint(0, (end_min - start_min) * 60)
            ticket_time = start_dt + timedelta(minutes=start_min, seconds=offset_sec)
            ctype, desc = rng.choice(type_pool)
            ticket_counter += 1
            tickets.append({
                "ticket_id": f"TKT-{ticket_counter}",
                "created_at": ticket_time.strftime("%Y-%m-%d %H:%M:%S"),
                "zone_code": "Zone-B",
                "complaint_type": ctype,
                "description": desc,
                "source_system": "Demo data — simulated civic feeds"
            })
            
    # Sort tickets chronologically
    tickets.sort(key=lambda x: x["created_at"])
    return tickets

def save_complaints_raw(filepath: str = "data/raw/complaints_raw.json"):
    """Generates and saves the raw complaint records to a JSON file."""
    data = generate_complaints_raw()
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return len(data)

if __name__ == "__main__":
    count = save_complaints_raw()
    print(f"Generated {count} raw complaint tickets in data/raw/complaints_raw.json")
