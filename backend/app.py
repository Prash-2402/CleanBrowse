from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import time
import threading
import traceback
import base64
from pathlib import Path

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
    REPORT_STATUS_ROUTE,
)
from backend.text_safety import score_text_safety
from backend.database import init_db, insert_event
from backend.alerts import trigger_desktop_alert
from backend.image_logic import moderator
from backend.reporting import get_dashboard_data
from backend.api_config import DASHBOARD_ROUTE

app = Flask(__name__)
CORS(app)

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
    
    # Desktop alerts removed — events are surfaced in the live dashboard feed
    
    return jsonify({"success": True, "event_id": event_id})


@app.get(REPORT_UNINSTALL_ROUTE)
def report_uninstall():
    event_id = insert_event(
        event_type="bypass_attempt", 
        url="Uninstall Detected", 
        snippet="The CleanBrowse extension has been disabled or uninstalled by the user.", 
        severity="high"
    )
    
    # Desktop alert removed — uninstall event is logged to DB and visible in dashboard
    
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
# Default to "Closed" until the first heartbeat arrives to avoid cold-start alerts.
LAST_HEARTBEAT_TIME = time.time()
LAST_ACTIVE_MODE = "Unknown"
ALERTTED_STALE = True  # Suppress until first heartbeat
HEARTBEAT_LOCK = threading.Lock()

# Browser state
# True  = heartbeat received, protection is ON
# False = browser_closing signal received OR cold start
BROWSER_OPEN = False

@app.post(HEARTBEAT_ROUTE)
def heartbeat():
    global LAST_HEARTBEAT_TIME, ALERTTED_STALE, LAST_ACTIVE_MODE, BROWSER_OPEN
    data = request.get_json(silent=True) or {}
    mode = data.get("activeMode", "Unknown")
    
    with HEARTBEAT_LOCK:
        if LAST_ACTIVE_MODE != "Unknown" and mode != LAST_ACTIVE_MODE:
            print(f"\n[ALERT] Safety Mode changed from {LAST_ACTIVE_MODE} to {mode}!")
        
        LAST_HEARTBEAT_TIME = time.time()
        LAST_ACTIVE_MODE = mode
        
        # Transition from CLOSED -> OPEN
        if not BROWSER_OPEN:
            print(f"\n[INFO] Browser connected. Protection monitoring started (Mode: {mode}).")
        BROWSER_OPEN = True
        
        # Transition from STALE -> ACTIVE
        if ALERTTED_STALE:
            # Check if this was a legitimate restore (not just the initial cold start)
            # We use a simple heuristic: if it's been more than 5s since start.
            print(f"\n[INFO] Heartbeat restored. Extension is back online (Mode: {mode}).")
        ALERTTED_STALE = False
    
    return jsonify({"status": "alive", "mode": mode})


@app.route(REPORT_STATUS_ROUTE, methods=["GET", "POST"])
def report_status():
    """Extension calls this to announce a graceful shutdown reason."""
    global BROWSER_OPEN, ALERTTED_STALE
    
    # Read from all possible sources: query params, form data (sendBeacon), or JSON (fetch)
    reason = (
        request.args.get("reason")           # query string (?reason=...)
        or request.form.get("reason")         # URLSearchParams body (sendBeacon)
        or (request.get_json(silent=True) or {}).get("reason")  # JSON body (fetch)
        or "unknown"
    )
    
    with HEARTBEAT_LOCK:
        print(f"\n[DEBUG] Status signal received: {reason}")
        if reason == "browser_closing":
            # Flip state immediately — watchdog will skip all checks until browser reopens
            BROWSER_OPEN = False
            ALERTTED_STALE = True  # Suppress watchdog until next heartbeat
            print(f"[INFO] Browser closing signal received. Watchdog paused until browser reopens.")
        elif reason == "extension_suspending":
            # Extension disabled — keep BROWSER_OPEN = True so watchdog fires the alert after timeout
            print(f"[INFO] Extension suspending signal received. Alert will trigger after {HEARTBEAT_TIMEOUT}s.")
    
    return jsonify({"status": "acknowledged", "reason": reason})

@app.get(DASHBOARD_ROUTE)
def dashboard():
    """Renders the parent dashboard with aggregated metrics."""
    data = get_dashboard_data()
    # Embed the logo as base64 so it works with Flask's template folder structure
    logo_b64 = ""
    try:
        logo_path = Path(__file__).parent / "static" / "logo.png"
        if logo_path.exists():
            logo_b64 = base64.b64encode(logo_path.read_bytes()).decode()
    except Exception:
        pass
    return render_template("dashboard.html", data=data, logo_b64=logo_b64)

@app.get("/api/recent-events")
def recent_events_api():
    """Lightweight polling endpoint for real-time alert feed updates."""
    from backend.database import get_db_connection
    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT id, event_type, url, snippet, severity, timestamp FROM events ORDER BY timestamp DESC LIMIT 50"
        ).fetchall()
        events = [
            {"id": r["id"], "type": r["event_type"], "url": r["url"] or "",
             "snippet": r["snippet"] or "", "severity": r["severity"], "time": r["timestamp"]}
            for r in rows
        ]
        return jsonify({"events": events})
    finally:
        conn.close()

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
    global LAST_HEARTBEAT_TIME, ALERTTED_STALE, BROWSER_OPEN
    
    check_interval = 10 # seconds
    last_check_time = time.time()
    
    while True:
        try:
            time.sleep(check_interval)
            now = time.time()
            
            # 1. Sleep Detection: Did the computer sleep?
            elapsed = now - last_check_time
            drift = elapsed - check_interval
            
            if drift > SLEEP_DRIFT_THRESHOLD:
                with HEARTBEAT_LOCK:
                    LAST_HEARTBEAT_TIME = now
                    ALERTTED_STALE = False
            else:
                with HEARTBEAT_LOCK:
                    # 2. If browser is closed, skip ALL checks — no alerting while browser is down.
                    #    BROWSER_OPEN flips back to True the instant the next heartbeat arrives.
                    if not BROWSER_OPEN:
                        pass  # Silently skip — browser is known to be closed
                    
                    elif not ALERTTED_STALE and (now - LAST_HEARTBEAT_TIME) > HEARTBEAT_TIMEOUT:
                        # Heartbeats stopped while browser is open — something is wrong
                        ALERTTED_STALE = True
                        try:
                            insert_event(
                                event_type="bypass_attempt",
                                url="Protection Disabled",
                                snippet="CleanBrowse stopped sending heartbeats while the browser was open. Extension may have been disabled or removed.",
                                severity="high"
                            )
                            # Desktop alert removed — bypass is logged to DB
                        except Exception as e:
                            print(f"Error in watchdog during alert: {e}")
            
            last_check_time = now
        except Exception as e:
            print(f"Watchdog loop encountered an error: {e}")
            traceback.print_exc()
            time.sleep(5)

# Start the watchdog in a background thread
monitor_thread = threading.Thread(target=watchdog_monitor, daemon=True)
monitor_thread.start()

def main() -> None:
    app.run(host=API_HOST, port=API_PORT, debug=API_DEBUG)


if __name__ == "__main__":
    main()