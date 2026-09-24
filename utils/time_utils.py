"""
time_utils.py - Timestamp Utilities for CityPulse

Provides consistent datetime parsing, formatting, and time binning across feeds.
"""

from datetime import datetime
import pandas as pd

def parse_timestamp(ts_val):
    """
    Safely parses an input timestamp (str, datetime, or pandas Timestamp)
    into a pandas Timestamp. Returns pd.NaT if parsing fails.
    """
    if ts_val is None or pd.isna(ts_val):
        return pd.NaT
    try:
        return pd.to_datetime(ts_val)
    except Exception:
        return pd.NaT

def floor_to_interval(ts, minutes: int = 5):
    """
    Floors a timestamp to the nearest minute interval (e.g., 5-min bins).
    Helps align asynchronous feeds into common analysis windows.
    """
    parsed = parse_timestamp(ts)
    if pd.isna(parsed):
        return pd.NaT
    return parsed.floor(f"{minutes}min")
