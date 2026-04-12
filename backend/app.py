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
)
from backend.text_safety import score_text_safety
from backend.database import init_db, insert_event
from backend.alerts import trigger_desktop_alert

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
        alert_msg = f"A {event_type} event was blocked at {url}"
        trigger_desktop_alert(alert_title, alert_msg)
    
    return jsonify({"success": True, "event_id": event_id})



def main() -> None:
    app.run(host=API_HOST, port=API_PORT, debug=API_DEBUG)


if __name__ == "__main__":
    main()
