"""
ui/google_map.py - Professional Google Maps JavaScript API Component for CityPulse

Renders an interactive Google Map with:
- Custom dark control-room cartography matching the CityPulse dashboard
- CityPulse municipal zone containment boundaries (colored by pulse health state)
- Civic anomaly event markers (differentiated by telemetry feed type and severity)
- Interactive InfoWindows showing zone metadata, readings, baselines, and empirical evidence
- Strict non-causation relationship disclaimer
- Clean legend and responsive container
- Secure API key retrieval via st.secrets["GOOGLE_MAPS_API_KEY"] without hardcoding or leaking secrets
- Seamless fallback to Folium/OpenStreetMap if the API key is not configured
"""

import os
import json
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import folium
from streamlit_folium import st_folium

from utils.geo_utils import CITY_NAME, CITY_CENTER, ZONES, get_zone_metadata

# ---------------------------------------------------------
# 1. Secure API Key Retrieval
# ---------------------------------------------------------
def get_google_maps_api_key() -> str | None:
    """
    Safely retrieves the Google Maps API key from Streamlit secrets or environment.
    Never prints or logs the key. Returns None if missing or placeholder.
    """
    # 1. Check Streamlit secrets
    try:
        if hasattr(st, "secrets") and "GOOGLE_MAPS_API_KEY" in st.secrets:
            key = str(st.secrets["GOOGLE_MAPS_API_KEY"]).strip()
            if key and key != "YOUR_KEY_HERE" and not key.startswith("YOUR_"):
                return key
    except Exception:
        pass
        
    # 2. Check environment variable
    env_key = os.environ.get("GOOGLE_MAPS_API_KEY", "").strip()
    if env_key and env_key != "YOUR_KEY_HERE" and not env_key.startswith("YOUR_"):
        return env_key
        
    return None


# ---------------------------------------------------------
# 2. Google Maps HTML / JavaScript Builder
# ---------------------------------------------------------
def build_google_maps_html(
    api_key: str,
    city_center: dict,
    zone_pulses: list[dict],
    anomalies_df: pd.DataFrame,
    alerts: list[dict],
    selected_zone: str = "All Zones"
) -> str:
    """
    Constructs the self-contained HTML/JS document embedding the Google Maps JavaScript API.
    All data is serialized as JSON and passed into the client-side Google Maps runtime.
    """
    # Zone Color Mapping
    zone_color_map = {
        "NORMAL": "#10B981",    # Emerald
        "ATTENTION": "#F59E0B", # Amber
        "ELEVATED": "#F97316",  # Orange
        "CRITICAL": "#EF4444"   # Crimson Red
    }
    
    # Telemetry Pin Color Mapping
    feed_color_map = {
        "rainfall_rate": "#38BDF8",   # Sky Blue
        "traffic_speed": "#EF4444",   # Crimson Red
        "transit_delay": "#F97316",   # Orange
        "311_incident": "#A855F7"     # Purple
    }
    
    # 1. Package Zones Data
    zones_data = []
    for zp in zone_pulses:
        zid = zp.get("zone", "")
        zmeta = get_zone_metadata(zid) or {}
        state = zp.get("pulse_state", "NORMAL")
        color = zone_color_map.get(state, "#64748B")
        
        # Collect related alert evidence for this zone
        zone_alerts = [a for a in alerts if a.get("zone") == zid]
        evidence_points = []
        relationship_text = "All civic signals within standard baseline tolerances."
        if zone_alerts:
            evidence_points = zone_alerts[0].get("evidence_points", [])
            why = zone_alerts[0].get("why_this_alert", {})
            relationship_text = why.get("relationship_statement", "Possible spatiotemporal association between co-occurring signals.")
            
        zones_data.append({
            "id": zid,
            "name": zmeta.get("name", zid),
            "description": zmeta.get("description", "Municipal Zone"),
            "lat": float(zmeta.get("latitude", city_center["latitude"])),
            "lng": float(zmeta.get("longitude", city_center["longitude"])),
            "state": state,
            "score": float(zp.get("pulse_score", 10.0)),
            "anomaly_count": int(zp.get("anomaly_count", 0)),
            "explanation": zp.get("explanation", ""),
            "color": color,
            "evidence": evidence_points,
            "relationship": relationship_text,
            "is_selected": (selected_zone == "All Zones" or selected_zone == zid)
        })
        
    # 2. Package Anomalies Data
    anomalies_data = []
    if not anomalies_df.empty:
        for _, anom in anomalies_df.iterrows():
            feed = anom.get("feed_type", "")
            color = feed_color_map.get(feed, "#94A3B8")
            sev = anom.get("anomaly_severity", "MODERATE")
            t_str = anom["timestamp"].strftime("%H:%M:%S") if isinstance(anom.get("timestamp"), pd.Timestamp) else str(anom.get("timestamp", ""))
            
            anomalies_data.append({
                "lat": float(anom.get("latitude", city_center["latitude"])),
                "lng": float(anom.get("longitude", city_center["longitude"])),
                "zone": str(anom.get("zone", "")),
                "feed_type": feed,
                "anomaly_type": str(anom.get("anomaly_type", "")).replace("_", " "),
                "val": float(anom.get("value", 0.0)),
                "unit": str(anom.get("unit", "")),
                "severity": sev,
                "deviation": float(anom.get("deviation", 0.0)),
                "rolling_mean": float(anom.get("rolling_mean", 0.0)),
                "timestamp": t_str,
                "explanation": str(anom.get("anomaly_explanation", "")),
                "color": color
            })

    # Center coords and zoom
    center_lat = float(city_center["latitude"])
    center_lng = float(city_center["longitude"])
    zoom_level = int(city_center.get("zoom_start", 12))
    
    # Adjust center if single zone filtered
    if selected_zone != "All Zones":
        sel_meta = get_zone_metadata(selected_zone)
        if sel_meta:
            center_lat = float(sel_meta["latitude"])
            center_lng = float(sel_meta["longitude"])
            zoom_level = 13

    zones_json = json.dumps(zones_data)
    anomalies_json = json.dumps(anomalies_data)

    # Google Maps Dark Theme JSON Style
    dark_styles_json = json.dumps([
        {"elementType": "geometry", "stylers": [{"color": "#0e1322"}]},
        {"elementType": "labels.text.stroke", "stylers": [{"color": "#0b0f19"}, {"weight": 3}]},
        {"elementType": "labels.text.fill", "stylers": [{"color": "#94a3b8"}]},
        {"featureType": "administrative", "elementType": "geometry.stroke", "stylers": [{"color": "#1e293b"}]},
        {"featureType": "administrative.land_parcel", "stylers": [{"visibility": "off"}]},
        {"featureType": "administrative.locality", "elementType": "labels.text.fill", "stylers": [{"color": "#cbd5e1"}]},
        {"featureType": "poi", "elementType": "labels.text.fill", "stylers": [{"color": "#64748b"}]},
        {"featureType": "poi.park", "elementType": "geometry", "stylers": [{"color": "#111827"}]},
        {"featureType": "road", "elementType": "geometry", "stylers": [{"color": "#1e293b"}]},
        {"featureType": "road", "elementType": "geometry.stroke", "stylers": [{"color": "#0b0f19"}]},
        {"featureType": "road", "elementType": "labels.text.fill", "stylers": [{"color": "#94a3b8"}]},
        {"featureType": "road.highway", "elementType": "geometry", "stylers": [{"color": "#24324a"}]},
        {"featureType": "road.highway", "elementType": "geometry.stroke", "stylers": [{"color": "#111827"}]},
        {"featureType": "road.highway", "elementType": "labels.text.fill", "stylers": [{"color": "#e2e8f0"}]},
        {"featureType": "transit", "elementType": "geometry", "stylers": [{"color": "#162032"}]},
        {"featureType": "transit.station", "elementType": "labels.text.fill", "stylers": [{"color": "#94a3b8"}]},
        {"featureType": "water", "elementType": "geometry", "stylers": [{"color": "#080c16"}]},
        {"featureType": "water", "elementType": "labels.text.fill", "stylers": [{"color": "#475569"}]}
    ])

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    <title>CityPulse Google Map</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        html, body {{ height: 100%; width: 100%; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0B0F19; overflow: hidden; }}
        #map {{ height: 100%; width: 100%; }}
        
        /* Map Legend Overlay */
        .map-legend {{
            position: absolute;
            bottom: 24px;
            left: 12px;
            background: rgba(17, 24, 39, 0.92);
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 8px;
            padding: 8px 12px;
            font-size: 11.5px;
            color: #CBD5E1;
            z-index: 10;
            backdrop-filter: blur(8px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
            max-width: 90%;
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
        }}
        .legend-group {{ display: flex; align-items: center; gap: 8px; }}
        .legend-dot {{ width: 10px; height: 10px; border-radius: 50%; display: inline-block; }}

        /* InfoWindow Custom Styling */
        .gm-style-iw {{
            background: #111827 !important;
            color: #F8FAFC !important;
            border-radius: 10px !important;
            padding: 0 !important;
            border: 1px solid rgba(255, 255, 255, 0.14) !important;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.6) !important;
        }}
        .gm-style-iw-d {{ overflow: auto !important; max-height: 320px !important; padding: 14px !important; }}
        .gm-style-iw-tc::after {{ background: #111827 !important; }}
        .gm-ui-hover-effect {{ filter: invert(1) !important; }}

        /* Popup Content Layout */
        .popup-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; border-bottom: 1px solid rgba(255, 255, 255, 0.1); padding-bottom: 6px; }}
        .popup-title {{ font-size: 14px; font-weight: 700; color: #F8FAFC; }}
        .popup-badge {{ padding: 2px 7px; border-radius: 4px; font-size: 10.5px; font-weight: 700; text-transform: uppercase; }}
        .popup-badge-CRITICAL {{ background: rgba(239, 68, 68, 0.25); color: #F87171; border: 1px solid #EF4444; }}
        .popup-badge-ELEVATED {{ background: rgba(249, 115, 22, 0.25); color: #FB923C; border: 1px solid #F97316; }}
        .popup-badge-ATTENTION {{ background: rgba(245, 158, 11, 0.25); color: #FBBF24; border: 1px solid #F59E0B; }}
        .popup-badge-NORMAL {{ background: rgba(16, 185, 129, 0.25); color: #34D399; border: 1px solid #10B981; }}
        .popup-meta {{ font-size: 11px; color: #94A3B8; margin-bottom: 6px; }}
        .popup-section-title {{ font-size: 11px; font-weight: 700; color: #94A3B8; text-transform: uppercase; margin: 8px 0 3px 0; }}
        .popup-evidence-list {{ list-style-type: none; padding-left: 0; font-size: 11.5px; color: #E2E8F0; }}
        .popup-evidence-list li {{ margin-bottom: 3px; padding-left: 10px; position: relative; }}
        .popup-evidence-list li::before {{ content: "•"; position: absolute; left: 0; color: #38BDF8; font-weight: bold; }}
        .popup-disclaimer {{ background: rgba(30, 41, 59, 0.7); border-left: 3px solid #64748B; padding: 6px 8px; font-size: 10.5px; color: #94A3B8; font-style: italic; margin-top: 8px; border-radius: 3px; }}

        /* Error Banner */
        #auth-error {{
            display: none;
            position: absolute;
            top: 20px;
            left: 20px;
            right: 20px;
            background: rgba(239, 68, 68, 0.95);
            color: white;
            padding: 14px 18px;
            border-radius: 8px;
            font-size: 13px;
            z-index: 100;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5);
        }}
    </style>
</head>
<body>
    <div id="auth-error">
        <strong>⚠️ Google Maps Authentication Failed:</strong> Please verify that your API key is enabled for Maps JavaScript API and has valid billing/referrer permissions in Google Cloud Console.
    </div>
    <div id="map"></div>

    <!-- Floating Map Legend -->
    <div class="map-legend">
        <div class="legend-group">
            <strong>Zones:</strong>
            <span><span class="legend-dot" style="background:#10B981;"></span> Normal</span>
            <span><span class="legend-dot" style="background:#F59E0B;"></span> Attention</span>
            <span><span class="legend-dot" style="background:#F97316;"></span> Elevated</span>
            <span><span class="legend-dot" style="background:#EF4444;"></span> Critical</span>
        </div>
        <div class="legend-group">
            <strong>Signals:</strong>
            <span><span class="legend-dot" style="background:#38BDF8;"></span> Rain</span>
            <span><span class="legend-dot" style="background:#EF4444;"></span> Traffic</span>
            <span><span class="legend-dot" style="background:#F97316;"></span> Delay</span>
            <span><span class="legend-dot" style="background:#A855F7;"></span> 311</span>
        </div>
    </div>

    <script>
        // Global Auth Failure Handler
        window.gm_authFailure = function() {{
            document.getElementById('auth-error').style.display = 'block';
        }};

        var zonesData = {zones_json};
        var anomaliesData = {anomalies_json};
        var darkMapStyles = {dark_styles_json};

        function initCityPulseMap() {{
            var centerPos = {{ lat: {center_lat}, lng: {center_lng} }};
            var map = new google.maps.Map(document.getElementById('map'), {{
                center: centerPos,
                zoom: {zoom_level},
                styles: darkMapStyles,
                mapTypeControl: true,
                mapTypeControlOptions: {{
                    style: google.maps.MapTypeControlStyle.DROPDOWN_MENU,
                    position: google.maps.ControlPosition.TOP_RIGHT
                }},
                streetViewControl: false,
                fullscreenControl: true,
                zoomControl: true,
                zoomControlOptions: {{
                    position: google.maps.ControlPosition.RIGHT_CENTER
                }}
            }});

            var activeInfoWindow = null;

            // 1. Plot Zone Containment Circles & Center Markers
            zonesData.forEach(function(zone) {{
                var isSelected = zone.is_selected;
                var fillOpacity = isSelected ? (zone.state === 'NORMAL' ? 0.14 : 0.28) : 0.05;
                var strokeOpacity = isSelected ? 0.85 : 0.2;
                var strokeWeight = zone.state === 'CRITICAL' ? 3 : 2;

                var zoneCircle = new google.maps.Circle({{
                    strokeColor: zone.color,
                    strokeOpacity: strokeOpacity,
                    strokeWeight: strokeWeight,
                    fillColor: zone.color,
                    fillOpacity: fillOpacity,
                    map: map,
                    center: {{ lat: zone.lat, lng: zone.lng }},
                    radius: 1550
                }});

                // Zone Center Label Marker
                var zoneMarker = new google.maps.Marker({{
                    position: {{ lat: zone.lat, lng: zone.lng }},
                    map: map,
                    title: zone.id + " - " + zone.name,
                    label: {{
                        text: zone.id,
                        color: "#F8FAFC",
                        fontSize: "11px",
                        fontWeight: "700"
                    }},
                    icon: {{
                        path: google.maps.SymbolPath.CIRCLE,
                        scale: 16,
                        fillColor: zone.color,
                        fillOpacity: 0.9,
                        strokeColor: "#0B0F19",
                        strokeWeight: 2
                    }}
                }});

                // Construct Zone InfoWindow HTML
                var evidenceItemsHtml = "";
                if (zone.evidence && zone.evidence.length > 0) {{
                    evidenceItemsHtml = "<div class='popup-section-title'>Empirical Telemetry Evidence:</div><ul class='popup-evidence-list'>";
                    zone.evidence.forEach(function(ev) {{
                        evidenceItemsHtml += "<li>" + ev + "</li>";
                    }});
                    evidenceItemsHtml += "</ul>";
                }}

                var zoneContent = "<div style='min-width:240px;'>" +
                    "<div class='popup-header'>" +
                        "<span class='popup-title'>" + zone.id + ": " + zone.name + "</span>" +
                        "<span class='popup-badge popup-badge-" + zone.state + "'>" + zone.state + "</span>" +
                    "</div>" +
                    "<div class='popup-meta'>📍 Lat: " + zone.lat.toFixed(4) + ", Lng: " + zone.lng.toFixed(4) + " &bull; Index: <b>" + Math.round(zone.score) + "/100</b></div>" +
                    "<div style='font-size:12px; color:#CBD5E1; margin-bottom:6px;'>" + zone.explanation + "</div>" +
                    evidenceItemsHtml +
                    "<div class='popup-disclaimer'>⚖️ <b>Spatiotemporal Association:</b> " + zone.relationship + "</div>" +
                "</div>";

                var zoneIW = new google.maps.InfoWindow({{
                    content: zoneContent
                }});

                function openZoneIW() {{
                    if (activeInfoWindow) activeInfoWindow.close();
                    zoneIW.open(map, zoneMarker);
                    activeInfoWindow = zoneIW;
                }}

                zoneMarker.addListener('click', openZoneIW);
                zoneCircle.addListener('click', openZoneIW);
            }});

            // 2. Plot Active Telemetry Anomaly Markers
            anomaliesData.forEach(function(anom) {{
                var isHigh = (anom.severity === "HIGH");
                var scaleSize = isHigh ? 8 : 6;
                var strokeW = isHigh ? 2.5 : 1.5;

                var marker = new google.maps.Marker({{
                    position: {{ lat: anom.lat, lng: anom.lng }},
                    map: map,
                    title: anom.anomaly_type + " (" + anom.severity + ")",
                    icon: {{
                        path: google.maps.SymbolPath.CIRCLE,
                        scale: scaleSize,
                        fillColor: anom.color,
                        fillOpacity: 1.0,
                        strokeColor: isHigh ? "#FFFFFF" : "#0B0F19",
                        strokeWeight: strokeW
                    }}
                }});

                var anomContent = "<div style='min-width:220px;'>" +
                    "<div class='popup-header'>" +
                        "<span class='popup-title'>" + anom.anomaly_type + "</span>" +
                        "<span class='popup-badge' style='background:" + anom.color + "33; color:" + anom.color + "; border:1px solid " + anom.color + ";'>" + anom.severity + "</span>" +
                    "</div>" +
                    "<div class='popup-meta'>⏱️ " + anom.timestamp + " &bull; Zone: <b>" + anom.zone + "</b></div>" +
                    "<div style='font-size:12.5px; color:#F8FAFC; margin-bottom:4px; font-family:monospace;'>" +
                        "Reading: <b>" + anom.val + " " + anom.unit + "</b> (baseline: " + anom.rolling_mean.toFixed(1) + ", dev: " + (anom.deviation >= 0 ? "+" : "") + anom.deviation.toFixed(1) + ")" +
                    "</div>" +
                    "<div style='font-size:11.5px; color:#94A3B8; line-height:1.4;'>" + anom.explanation + "</div>" +
                    "<div class='popup-meta' style='margin-top:6px;'>📍 Coordinates: " + anom.lat.toFixed(4) + ", " + anom.lng.toFixed(4) + "</div>" +
                "</div>";

                var anomIW = new google.maps.InfoWindow({{
                    content: anomContent
                }});

                marker.addListener('click', function() {{
                    if (activeInfoWindow) activeInfoWindow.close();
                    anomIW.open(map, marker);
                    activeInfoWindow = anomIW;
                }});
            }});
        }}
    </script>
    <script src="https://maps.googleapis.com/maps/api/js?key={api_key}&callback=initCityPulseMap&v=weekly" async defer></script>
</body>
</html>"""
    return html_content


# ---------------------------------------------------------
# 3. Folium / OpenStreetMap Fallback Renderer
# ---------------------------------------------------------
def render_folium_fallback(
    city_center: dict,
    zone_pulses: list[dict],
    anomalies_df: pd.DataFrame,
    selected_zone: str = "All Zones",
    map_style: str = "CartoDB Dark Matter",
    height: int = 480
):
    """Renders the existing Folium / OpenStreetMap map as a reliable offline/fallback engine."""
    tile_name = "CartoDB dark_matter" if "Dark" in map_style else "CartoDB positron"
    
    m = folium.Map(
        location=[city_center["latitude"], city_center["longitude"]],
        zoom_start=city_center["zoom_start"],
        tiles=tile_name
    )
    
    zone_color_map = {
        "NORMAL": "#10B981",
        "ATTENTION": "#F59E0B",
        "ELEVATED": "#F97316",
        "CRITICAL": "#EF4444"
    }
    
    # 1. Plot Zone Health Rings
    for zp in zone_pulses:
        zid = zp["zone"]
        zmeta = get_zone_metadata(zid) or {}
        color = zone_color_map.get(zp["pulse_state"], "#64748B")
        
        if selected_zone != "All Zones" and zid != selected_zone:
            ring_opacity = 0.05
            weight = 1
        else:
            ring_opacity = 0.24 if zp["pulse_state"] != "NORMAL" else 0.12
            weight = 3 if zp["pulse_state"] == "CRITICAL" else 2
        
        folium.Circle(
            location=[zmeta.get("latitude", city_center["latitude"]), zmeta.get("longitude", city_center["longitude"])],
            radius=1600,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=ring_opacity,
            weight=weight,
            tooltip=f"{zid} ({zmeta.get('name', zid)}): {zp['pulse_state']} | Score: {zp['pulse_score']}/100",
            popup=folium.Popup(f"""
            <div style="font-family:sans-serif; min-width:190px;">
                <b style="font-size:14px;">{zid}: {zmeta.get('name', zid)}</b><br/>
                Status: <b style="color:{color};">{zp['pulse_state']}</b> ({zp['pulse_score']:.0f}/100)<br/>
                Active Anomalies: <b>{zp['anomaly_count']}</b><br/>
                <hr style="margin:6px 0; border:0; border-top:1px solid #ccc;"/>
                <span style="font-size:12px; color:#555;">{zp['explanation']}</span>
            </div>
            """, max_width=300)
        ).add_to(m)
        
    # 2. Plot Active Telemetry Anomaly Markers
    feed_colors = {
        "rainfall_rate": "#38BDF8",   # Sky Blue
        "traffic_speed": "#EF4444",   # Crimson Red
        "transit_delay": "#F97316",   # Orange
        "311_incident": "#A855F7"     # Purple
    }
    
    if not anomalies_df.empty:
        for _, anom in anomalies_df.iterrows():
            lat = anom["latitude"]
            lon = anom["longitude"]
            feed = anom["feed_type"]
            atype = anom["anomaly_type"]
            val = anom["value"]
            unit = anom["unit"]
            sev = anom["anomaly_severity"]
            marker_color = feed_colors.get(feed, "#94A3B8")
            
            folium.CircleMarker(
                location=[lat, lon],
                radius=7,
                color=marker_color,
                fill=True,
                fill_color=marker_color,
                fill_opacity=0.9,
                weight=2,
                tooltip=f"{atype} ({sev}) - {val} {unit}",
                popup=folium.Popup(f"""
                <div style="font-family:sans-serif; min-width:180px;">
                    <b>{atype}</b> ({sev})<br/>
                    Zone: <b>{anom['zone']}</b><br/>
                    Observed: <b>{val} {unit}</b><br/>
                    Time: {anom['timestamp'].strftime('%H:%M:%S') if isinstance(anom['timestamp'], pd.Timestamp) else str(anom['timestamp'])}<br/>
                    <i>{anom['anomaly_explanation']}</i>
                </div>
                """, max_width=280)
            ).add_to(m)
            
    st_folium(m, height=height, use_container_width=True, returned_objects=[])
    
    # Legend
    st.markdown("""<div style="display:flex; justify-content:space-between; flex-wrap:wrap; background:#111827; border:1px solid rgba(255,255,255,0.08); border-radius:8px; padding:8px 14px; font-size:12px; color:#94A3B8; margin-top:6px;">
<div><strong>Zones:</strong> <span style="color:#10B981;">● Normal</span> &nbsp;<span style="color:#F59E0B;">● Attention</span> &nbsp;<span style="color:#F97316;">● Elevated</span> &nbsp;<span style="color:#EF4444;">● Critical</span></div>
<div><strong>Telemetry Pins:</strong> <span style="color:#38BDF8;">● Rain Surge</span> &nbsp;<span style="color:#EF4444;">● Traffic Slowdown</span> &nbsp;<span style="color:#F97316;">● Transit Delay</span> &nbsp;<span style="color:#A855F7;">● 311 Report</span></div>
</div>""", unsafe_allow_html=True)


# ---------------------------------------------------------
# 4. Master Map Section Orchestrator
# ---------------------------------------------------------
def render_citypulse_map(
    zone_pulses: list[dict],
    anomalies_df: pd.DataFrame,
    alerts: list[dict],
    selected_zone: str = "All Zones",
    map_style: str = "CartoDB Dark Matter",
    preferred_engine: str = "auto",
    height: int = 490
):
    """
    Main map orchestrator for CityPulse.
    - If Google Maps API key is configured: renders Google Maps JavaScript API.
    - If Google Maps API key is missing: displays informative guidance and renders Folium fallback.
    - Never prints or exposes secrets.
    """
    api_key = get_google_maps_api_key()
    has_gmaps_key = bool(api_key)
    
    # Engine determination
    use_google_maps = has_gmaps_key and (preferred_engine in ["auto", "google_maps"])
    
    if use_google_maps:
        st.caption(f"Interactive Google Maps JavaScript API with zone containment rings and active multi-feed telemetry pins.")
        
        map_html = build_google_maps_html(
            api_key=api_key,
            city_center=CITY_CENTER,
            zone_pulses=zone_pulses,
            anomalies_df=anomalies_df,
            alerts=alerts,
            selected_zone=selected_zone
        )
        components.html(map_html, height=height, scrolling=False)
        
    else:
        # Fallback to OpenStreetMap / Folium
        if not has_gmaps_key:
            st.info("💡 **Google Maps API key is not configured.** Displaying OpenStreetMap / Folium as default fallback. (To enable Google Maps, add `GOOGLE_MAPS_API_KEY` to `.streamlit/secrets.toml`).")
        else:
            st.caption(f"Interactive OpenStreetMap engine with zone containment rings.")
            
        render_folium_fallback(
            city_center=CITY_CENTER,
            zone_pulses=zone_pulses,
            anomalies_df=anomalies_df,
            selected_zone=selected_zone,
            map_style=map_style,
            height=height
        )
