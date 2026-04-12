from flask import Flask, jsonify, request

from backend.api_config import (
    ANALYZE_TEXT_ROUTE,
    REPORT_EVENT_ROUTE,
    API_DEBUG,
    API_HOST,
    API_PORT,
    HOME_EXAMPLE_TEXT,
    HOME_MESSAGE,
    ROOT_ROUTE,
    TEXT_FIELD,
    REPORT_UNINSTALL_ROUTE,
    HEARTBEAT_ROUTE,
    HEARTBEAT_TIMEOUT,
    SLEEP_DRIFT_THRESHOLD,
    ANALYZE_IMAGE_ROUTE,
)
import time
import threading
import traceback
from backend.text_safety import score_text_safety
from backend.database import init_db, insert_event
from backend.alerts import trigger_desktop_alert
from backend.image_logic import moderator

app = Flask(__name__)

# Initialize the SQLite Database
init_db()

@app.get(ROOT_ROUTE)
def home():
    return jsonify(
        {
            "message": HOME_MESSAGE,
            "endpoint": ANALYZE_TEXT_ROUTE,
            "method": "POST",
            "example_request": {TEXT_FIELD: HOME_EXAMPLE_TEXT},
        }
    )


@app.post(ANALYZE_TEXT_ROUTE)
def analyze_text():
    data = request.get_json(silent=True)
    if not data or TEXT_FIELD not in data:
        return jsonify({"error": f'Request body must include "{TEXT_FIELD}".'}), 400

    return jsonify(score_text_safety(data[TEXT_FIELD]))


@app.get("/cache-stats")
def cache_stats():
    from backend.text_safety import _evaluate_text_cached
    info = _evaluate_text_cached.cache_info()
    return jsonify({
        "hits": info.hits,
        "misses": info.misses,
        "maxsize": info.maxsize,
        "currsize": info.currsize
    })


@app.post(REPORT_EVENT_ROUTE)
def report_event():
    data = request.get_json(silent=True)
    if not data or "event_type" not in data or "url" not in data:
        return jsonify({"error": 'Request body must include "event_type" and "url".'}), 400
    
    event_type = str(data.get("event_type"))
    url = str(data.get("url"))
    snippet = str(data.get("snippet", ""))
    severity = str(data.get("severity", "medium"))
    
    event_id = insert_event(event_type=event_type, url=url, snippet=snippet, severity=severity)
    
    # Simulate a Remote Parent push notification using Windows Desktop alerts
    if severity == "high":
        alert_title = "CleanBrowse Security Alert"
        if event_type == "bypass_attempt":
            alert_msg = f"Security Warning: {url}"
        else:
            alert_msg = f"A {event_type} event was blocked at {url}"
        trigger_desktop_alert(alert_title, alert_msg)
    
    return jsonify({"success": True, "event_id": event_id})


@app.get(REPORT_UNINSTALL_ROUTE)
def report_uninstall():
    event_id = insert_event(
        event_type="bypass_attempt", 
        url="Uninstall Detected", 
        snippet="The CleanBrowse extension has been disabled or uninstalled by the user.", 
        severity="high"
    )
    
    alert_title = "CleanBrowse Security Alert"
    alert_msg = "CleanBrowse Extension was uninstalled or disabled!"
    trigger_desktop_alert(alert_title, alert_msg)
    
    return """
    <html>
        <head><title>CleanBrowse Removed</title></head>
        <body style="font-family: sans-serif; text-align: center; margin-top: 50px;">
            <h2>CleanBrowse Extension has been removed.</h2>
            <p>This action has been logged.</p>
        </body>
    </html>
    """, 200

# Global state for heartbeat monitoring
LAST_HEARTBEAT_TIME = time.time()
LAST_ACTIVE_MODE = "Unknown"
ALERTTED_STALE = False
HEARTBEAT_LOCK = threading.Lock()

@app.post(HEARTBEAT_ROUTE)
def heartbeat():
    global LAST_HEARTBEAT_TIME, ALERTTED_STALE, LAST_ACTIVE_MODE
    data = request.get_json(silent=True) or {}
    mode = data.get("activeMode", "Unknown")
    
    with HEARTBEAT_LOCK:
        if LAST_ACTIVE_MODE != "Unknown" and mode != LAST_ACTIVE_MODE:
            print(f"\n[ALERT] Safety Mode changed from {LAST_ACTIVE_MODE} to {mode}!")
        
        LAST_HEARTBEAT_TIME = time.time()
        LAST_ACTIVE_MODE = mode
        if ALERTTED_STALE:
            print(f"\n[INFO] Heartbeat restored. Extension is back online (Mode: {mode}).")
        ALERTTED_STALE = False
    
    return jsonify({"status": "alive", "mode": mode})

@app.post(ANALYZE_IMAGE_ROUTE)
def analyze_image():
    # To be implemented in Phase 10
    data = request.get_json(silent=True)
    if not data or "image_url" not in data:
        return jsonify({"error": 'Request body must include "image_url".'}), 400
    
    # Hybrid Tier 1-3 analysis
    image_url = data.get("image_url")
    alt_text = data.get("alt_text", "")
    title = data.get("title", "")
    
    result = moderator.analyze(image_url, alt_text, title)
    return jsonify(result)

def watchdog_monitor():
    global LAST_HEARTBEAT_TIME, ALERTTED_STALE
    
    check_interval = 10 # seconds (High responsiveness)
    last_check_time = time.time()
    
    while True:
        try:
            time.sleep(check_interval)
            now = time.time()
            
            # 1. Sleep Detection: Did the computer sleep?
            elapsed = now - last_check_time
            drift = elapsed - check_interval
            
            if drift > SLEEP_DRIFT_THRESHOLD:
                # System likely slept. Reset the clock to avoid fake alert.
                with HEARTBEAT_LOCK:
                    LAST_HEARTBEAT_TIME = now
                    ALERTTED_STALE = False
            else:
                # 2. Tamper Detection: Is the heartbeat missing while system is awake?
                with HEARTBEAT_LOCK:
                    if not ALERTTED_STALE and (now - LAST_HEARTBEAT_TIME) > HEARTBEAT_TIMEOUT:
                        ALERTTED_STALE = True
                        try:
                            event_id = insert_event(
                                event_type="bypass_attempt", 
                                url="Protection Disabled", 
                                snippet="CleanBrowse stopped sending heatbeats while system was active. It was likely turned off.", 
                                severity="high"
                            )
                            trigger_desktop_alert(
                                "CleanBrowse Security Alert", 
                                "CRITICAL: Protection Disabled! Extension was turned off while computer is active."
                            )
                        except Exception as e:
                            print(f"Error in watchdog during alert: {e}")
            
            last_check_time = now
        except Exception as e:
            print(f"Watchdog loop encountered an error: {e}")
            traceback.print_exc()
            time.sleep(5) # Avoid rapid-fire crashing

# Start the watchdog in a background thread
monitor_thread = threading.Thread(target=watchdog_monitor, daemon=True)
monitor_thread.start()

def main() -> None:
    app.run(host=API_HOST, port=API_PORT, debug=API_DEBUG)


if __name__ == "__main__":
    main()
