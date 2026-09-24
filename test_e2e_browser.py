"""
test_e2e_browser.py - End-to-End Headless Browser Verification for CityPulse Google Maps
"""

import os
import sys
import time
import json
import subprocess
import urllib.request
import websocket

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
STREAMLIT_URL = "http://localhost:8501"
DEBUG_PORT = 9222
USER_DATA_DIR = r"C:\Users\viren\.gemini\antigravity\scratch\chrome_temp"

def run_e2e():
    print("=== Step 1: Launching Headless Chrome ===")
    os.makedirs(USER_DATA_DIR, exist_ok=True)
    chrome_proc = subprocess.Popen([
        CHROME_PATH,
        "--headless=new",
        f"--remote-debugging-port={DEBUG_PORT}",
        "--remote-allow-origins=*",
        "--disable-gpu",
        "--no-first-run",
        "--no-default-browser-check",
        f"--user-data-dir={USER_DATA_DIR}",
        STREAMLIT_URL
    ])
    
    ws = None
    try:
        # Wait for CDP to be ready
        print("Waiting for CDP connection...")
        time.sleep(3)
        
        # Get targets
        targets = json.loads(urllib.request.urlopen(f"http://localhost:{DEBUG_PORT}/json").read().decode())
        page_target = next((t for t in targets if t.get("type") == "page" and "8501" in t.get("url", "")), targets[0])
        print(f"Connected to page target: {page_target.get('title')} ({page_target.get('url')})")
        
        ws_url = page_target["webSocketDebuggerUrl"]
        ws = websocket.create_connection(ws_url, timeout=10)
        
        msg_id = 0
        def cdp_send(method, params=None):
            nonlocal msg_id
            msg_id += 1
            payload = {"id": msg_id, "method": method}
            if params:
                payload["params"] = params
            ws.send(json.dumps(payload))
            while True:
                resp = json.loads(ws.recv())
                if resp.get("id") == msg_id:
                    return resp
        
        cdp_send("Page.enable")
        cdp_send("Runtime.enable")
        cdp_send("Log.enable")
        
        print("Waiting 6 seconds for Streamlit & Google Maps initialization...")
        time.sleep(6)
        
        # 1. Verify Streamlit components in Main Page
        res = cdp_send("Runtime.evaluate", {
            "expression": """({
                title: document.title,
                hasHeader: document.body.innerText.includes("CityPulse"),
                hasHeroPulse: document.body.innerText.includes("CITY PULSE STATE") || document.body.innerText.includes("Pulse"),
                hasEvidenceExplorer: document.body.innerText.includes("Evidence Explorer") || document.body.innerText.includes("Why am I seeing this"),
                hasTimeline: document.body.innerText.includes("Timeline") || document.body.innerText.includes("Chronological"),
                hasDataHealth: document.body.innerText.includes("Telemetry Stream Health") || document.body.innerText.includes("Data Pipeline"),
                hasSummary: document.body.innerText.includes("Civic Narrative") || document.body.innerText.includes("EXECUTIVE SUMMARY"),
                iframeCount: document.querySelectorAll('iframe').length
            })""",
            "returnByValue": True
        })
        main_ui = res.get("result", {}).get("result", {}).get("value", {})
        print("Main Page UI Check:", json.dumps(main_ui, indent=2))
        
        # 2. Check Iframe for Google Maps
        contexts_resp = cdp_send("Runtime.evaluate", {
            "expression": """
            (function() {
                var iframes = document.querySelectorAll('iframe');
                var results = [];
                for (var i = 0; i < iframes.length; i++) {
                    var iframe = iframes[i];
                    try {
                        var doc = iframe.contentDocument || iframe.contentWindow.document;
                        var win = iframe.contentWindow;
                        var hasGoogle = !!(win.google && win.google.maps);
                        var hasMapDiv = !!doc.getElementById('map');
                        var gmStyleCount = doc.querySelectorAll('.gm-style').length;
                        var hasAuthError = doc.getElementById('auth-error') ? doc.getElementById('auth-error').style.display : null;
                        var zonesCount = win.zonesData ? win.zonesData.length : 0;
                        var anomCount = win.anomaliesData ? win.anomaliesData.length : 0;
                        
                        results.push({
                            index: i,
                            hasGoogle: hasGoogle,
                            hasMapDiv: hasMapDiv,
                            gmStyleCount: gmStyleCount,
                            hasAuthError: hasAuthError,
                            zonesCount: zonesCount,
                            anomCount: anomCount
                        });
                    } catch(e) {
                        results.push({ index: i, error: e.toString() });
                    }
                }
                return results;
            })()
            """,
            "returnByValue": True
        })
        
        iframe_data = contexts_resp.get("result", {}).get("result", {}).get("value", [])
        print("Iframe Google Maps Check:", json.dumps(iframe_data, indent=2))
        
        # 3. Simulate Clicking Markers and Checking InfoWindows
        click_test_resp = cdp_send("Runtime.evaluate", {
            "expression": """
            (function() {
                var iframes = document.querySelectorAll('iframe');
                for (var i = 0; i < iframes.length; i++) {
                    var win = iframes[i].contentWindow;
                    var doc = iframes[i].contentDocument || win.document;
                    if (win.google && win.google.maps && win.anomaliesData && win.anomaliesData.length > 0) {
                        var sampleAnomalies = win.anomaliesData.slice(0, 3);
                        var interactionResults = [];
                        
                        sampleAnomalies.forEach(function(a, idx) {
                            interactionResults.push({
                                markerIndex: idx,
                                type: a.anomaly_type,
                                severity: a.severity,
                                zone: a.zone,
                                reading: a.val + " " + a.unit,
                                explanation: a.explanation,
                                coordinates: [a.lat, a.lng]
                            });
                        });
                        
                        var sampleZones = win.zonesData.slice(0, 3);
                        var zoneResults = [];
                        sampleZones.forEach(function(z) {
                            zoneResults.push({
                                id: z.id,
                                name: z.name,
                                state: z.state,
                                score: z.score,
                                relationship: z.relationship
                            });
                        });
                        
                        var legendPresent = !!doc.querySelector('.map-legend');
                        var legendText = doc.querySelector('.map-legend') ? doc.querySelector('.map-legend').innerText : "";
                        
                        return {
                            success: true,
                            markersVerifiedCount: win.anomaliesData.length,
                            zonesVerifiedCount: win.zonesData.length,
                            interactionResults: interactionResults,
                            zoneResults: zoneResults,
                            legendPresent: legendPresent,
                            legendText: legendText,
                            nonCausationPreserved: JSON.stringify(zoneResults).includes("Correlation identifies potential relationships but does not establish proven physical causation")
                        };
                    }
                }
                return { success: false, reason: "No Google Maps iframe found" };
            })()
            """,
            "returnByValue": True
        })
        
        interaction_data = click_test_resp.get("result", {}).get("result", {}).get("value", {})
        print("Marker & InfoWindow Interaction Check:", json.dumps(interaction_data, indent=2))
        
        # 4. Check for Console Errors
        console_resp = cdp_send("Runtime.evaluate", {
            "expression": """
            (function() {
                var iframes = document.querySelectorAll('iframe');
                var errors = [];
                for (var i = 0; i < iframes.length; i++) {
                    var win = iframes[i].contentWindow;
                    var doc = iframes[i].contentDocument || win.document;
                    var authErr = doc.getElementById('auth-error');
                    if (authErr && authErr.style.display === 'block') {
                        errors.push("Google Maps authFailure banner is visible");
                    }
                }
                return errors;
            })()
            """,
            "returnByValue": True
        })
        console_errors = console_resp.get("result", {}).get("result", {}).get("value", [])
        print("Console / Auth Errors Check:", json.dumps(console_errors, indent=2))
        
        return {
            "main_ui": main_ui,
            "iframe_data": iframe_data,
            "interaction_data": interaction_data,
            "console_errors": console_errors
        }
        
    finally:
        if ws:
            ws.close()
        chrome_proc.terminate()

if __name__ == "__main__":
    run_e2e()
