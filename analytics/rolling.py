"""
rolling.py - Rolling Window Analytics for CityPulse

Calculates temporal baselines and moving statistics partitioned by (zone, feed_type):
- current_value: latest reading
- rolling_mean: moving baseline over rolling window (e.g. 15 minutes)
- rolling_std: variance/spread
- deviation: difference between current reading and rolling mean
- pct_change: percentage deviation from baseline
- recent_change: change compared to immediate previous observation
- rolling_count: event density in the window (especially for 311 complaints)

Designed for simplicity, explainability, and defensive student presentations.
"""

import pandas as pd
import numpy as np

def compute_rolling_metrics(
    df: pd.DataFrame,
    window_minutes: int = 15,
    min_periods: int = 1
) -> pd.DataFrame:
    """
    Computes rolling window statistics for each (zone, feed_type) group.
    
    Parameters:
        df: DataFrame conforming to CityPulse Common Data Model.
        window_minutes: Rolling duration in minutes (default: 15).
        min_periods: Minimum observations required before producing a baseline.
        
    Returns:
        DataFrame enriched with rolling analytics columns:
        ['rolling_mean', 'rolling_std', 'deviation', 'pct_change', 'recent_change', 'rolling_count']
    """
    if df.empty:
        return df.copy()
        
    df_sorted = df.copy()
    df_sorted["timestamp"] = pd.to_datetime(df_sorted["timestamp"])
    df_sorted = df_sorted.sort_values(by=["zone", "feed_type", "timestamp"]).reset_index(drop=True)
    
    # Pre-allocate result columns
    df_sorted["rolling_mean"] = 0.0
    df_sorted["rolling_std"] = 0.0
    df_sorted["deviation"] = 0.0
    df_sorted["pct_change"] = 0.0
    df_sorted["recent_change"] = 0.0
    df_sorted["rolling_count"] = 1.0
    
    enriched_groups = []
    
    # Group by zone and feed_type so weather in Zone-A does not mix with Zone-B, etc.
    for (zone, feed_type), group in df_sorted.groupby(["zone", "feed_type"], sort=False):
        group = group.copy()
        
        # If feed is 311 complaints, aggregate event counts over time window
        if feed_type == "311_incident":
            # For complaints, each row is an event ticket.
            # We compute how many complaints occurred in the past `window_minutes`.
            window_counts = []
            timestamps = group["timestamp"].tolist()
            
            for i, ts in enumerate(timestamps):
                window_start = ts - pd.Timedelta(minutes=window_minutes)
                # Count events in (ts - window_minutes, ts]
                count = sum(1 for t in timestamps[:i + 1] if t >= window_start)
                window_counts.append(count)
                
            group["rolling_count"] = window_counts
            group["rolling_mean"] = group["rolling_count"].rolling(window=3, min_periods=1).mean().round(2)
            group["rolling_std"] = group["rolling_count"].rolling(window=3, min_periods=1).std().fillna(0.0).round(2)
            group["deviation"] = (group["rolling_count"] - group["rolling_mean"]).round(2)
            group["recent_change"] = group["rolling_count"].diff().fillna(0.0).round(2)
            group["pct_change"] = np.where(
                group["rolling_mean"] > 0,
                ((group["rolling_count"] - group["rolling_mean"]) / group["rolling_mean"] * 100.0).round(1),
                0.0
            )
        else:
            # Periodic continuous telemetry (rainfall_rate, traffic_speed, transit_delay)
            # Use pandas rolling calculation with time window
            group_indexed = group.set_index("timestamp")
            
            r_mean = group_indexed["value"].rolling(f"{window_minutes}min", min_periods=min_periods).mean()
            r_std = group_indexed["value"].rolling(f"{window_minutes}min", min_periods=min_periods).std().fillna(0.0)
            
            # Map back to group
            group["rolling_mean"] = r_mean.values.round(2)
            group["rolling_std"] = r_std.values.round(2)
            group["deviation"] = (group["value"] - group["rolling_mean"]).round(2)
            group["recent_change"] = group["value"].diff().fillna(0.0).round(2)
            
            # Safe percentage change against baseline
            denom = np.where(np.abs(group["rolling_mean"]) > 0.01, group["rolling_mean"], np.nan)
            group["pct_change"] = np.where(
                ~np.isnan(denom),
                ((group["value"] - group["rolling_mean"]) / denom * 100.0).round(1),
                0.0
            )
            group["rolling_count"] = 1.0
            
        enriched_groups.append(group)
        
    result_df = pd.concat(enriched_groups, ignore_index=True)
    # Restore original chronological sort
    result_df = result_df.sort_values(by="timestamp").reset_index(drop=True)
    return result_df

if __name__ == "__main__":
    import os
    sample_path = "data/processed/unified_civic_data.csv"
    if os.path.exists(sample_path):
        df_raw = pd.read_csv(sample_path)
        df_rolling = compute_rolling_metrics(df_raw, window_minutes=15)
        print("Rolling metrics computed successfully!")
        print("Columns added:", ['rolling_mean', 'rolling_std', 'deviation', 'pct_change', 'recent_change', 'rolling_count'])
        print("\nZone-B Traffic Speed Sample:")
        zb = df_rolling[(df_rolling['zone'] == 'Zone-B') & (df_rolling['feed_type'] == 'traffic_speed')]
        print(zb[['timestamp', 'value', 'rolling_mean', 'deviation', 'pct_change']].head(8))
