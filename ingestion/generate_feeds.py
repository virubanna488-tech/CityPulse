"""
generate_feeds.py - Master Feed Generator for CityPulse

Generates all 3 raw feeds (weather, traffic, complaints) into data/raw/.
Guarantees deterministic, reproducible simulation for AMIHACKS 1.0 demonstration.
"""

import sys
import os

# Ensure the root directory is on Python path so module imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ingestion.weather import save_weather_raw
from ingestion.traffic import save_traffic_raw
from ingestion.complaints import save_complaints_raw

def run_all_ingestion(raw_dir: str = "data/raw"):
    """Runs generation for all 3 feeds and saves them to raw_dir."""
    os.makedirs(raw_dir, exist_ok=True)
    
    weather_file = os.path.join(raw_dir, "weather_raw.json")
    traffic_file = os.path.join(raw_dir, "traffic_raw.csv")
    complaints_file = os.path.join(raw_dir, "complaints_raw.json")
    
    w_count = save_weather_raw(weather_file)
    t_count = save_traffic_raw(traffic_file)
    c_count = save_complaints_raw(complaints_file)
    
    return {
        "weather_records": w_count,
        "traffic_records": t_count,
        "complaints_records": c_count,
        "weather_path": weather_file,
        "traffic_path": traffic_file,
        "complaints_path": complaints_file
    }

if __name__ == "__main__":
    results = run_all_ingestion()
    print("====================================================")
    print(">>> CITYPULSE RAW FEED GENERATION COMPLETED <<<")
    print("====================================================")
    print(f" Weather Feed:    {results['weather_records']} records -> {results['weather_path']}")
    print(f" Traffic Feed:    {results['traffic_records']} records -> {results['traffic_path']}")
    print(f" Complaints Feed: {results['complaints_records']} records -> {results['complaints_path']}")
    print(" All feeds labeled: 'Demo data — simulated civic feeds'")
    print("====================================================")
