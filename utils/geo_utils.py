"""
geo_utils.py - Geographic Definitions and Utilities for CityPulse (Jaipur)

Defines civic zones and geographic center coordinates for Jaipur, Rajasthan.
Used by feed generation, normalization, spatial correlation, and mapping.
"""

CITY_NAME = "Jaipur"
CITY_CENTER = {
    "latitude": 26.9124,
    "longitude": 75.7873,
    "zoom_start": 12
}

# 6 defined civic zones across Jaipur, Rajasthan
ZONES = {
    "Zone-A": {
        "name": "Walled City / Pink City",
        "latitude": 26.9239,
        "longitude": 75.8267,
        "description": "Johari Bazaar, Badi Chaupar, historic dense commercial core"
    },
    "Zone-B": {
        "name": "MI Road & Ajmer Flyover Corridor",
        "latitude": 26.9157,
        "longitude": 75.7950,
        "description": "Low-lying commercial artery & transit junction (Storm Demo Zone)"
    },
    "Zone-C": {
        "name": "Malviya Nagar & Gaurav Tower",
        "latitude": 26.8530,
        "longitude": 75.8050,
        "description": "Commercial offices, retail, and tech hub"
    },
    "Zone-D": {
        "name": "Mansarovar & Metro Corridor",
        "latitude": 26.8640,
        "longitude": 75.7600,
        "description": "Dense residential neighborhoods and metro transit stations"
    },
    "Zone-E": {
        "name": "Vaishali Nagar & Khatipura",
        "latitude": 26.9080,
        "longitude": 75.7420,
        "description": "Residential district and west arterial connector"
    },
    "Zone-F": {
        "name": "Sitapura Industrial & Airport Link",
        "latitude": 26.8170,
        "longitude": 75.8150,
        "description": "Industrial zone, university corridor, and southern airport connector"
    }
}

def get_zone_list():
    """Return a list of all zone identifiers."""
    return list(ZONES.keys())

def get_zone_coords(zone_id: str):
    """Return (latitude, longitude) for a given zone ID, or (None, None) if unknown."""
    zone = ZONES.get(zone_id)
    if zone:
        return zone["latitude"], zone["longitude"]
    return None, None

def get_zone_metadata(zone_id: str):
    """Return full dictionary of metadata for a zone."""
    return ZONES.get(zone_id, None)
