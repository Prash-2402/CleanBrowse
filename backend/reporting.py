import sqlite3
from datetime import datetime, timedelta
from backend.database import get_db_connection

def get_dashboard_data():
    """Aggregates data for the parent dashboard."""
    conn = get_db_connection()
    try:
        # 1. Overall Totals by Type
        stats_rows = conn.execute(
            "SELECT event_type, COUNT(*) as count FROM events GROUP BY event_type"
        ).fetchall()
        stats = {row["event_type"]: row["count"] for row in stats_rows}

        # 2. Overall Totals by Severity
        severity_rows = conn.execute(
            "SELECT severity, COUNT(*) as count FROM events GROUP BY severity"
        ).fetchall()
        severity_stats = {row["severity"]: row["count"] for row in severity_rows}

        # 3. Daily Trends (Last 7 Days)
        daily_rows = conn.execute(
            """
            SELECT strftime('%Y-%m-%d', timestamp) as date, COUNT(*) as count
            FROM events
            WHERE timestamp >= datetime('now', '-7 days')
            GROUP BY date
            ORDER BY date ASC
            """
        ).fetchall()
        daily_trends = {row["date"]: row["count"] for row in daily_rows}

        # Fill in missing days for the graph
        filled_daily = []
        for i in range(7):
            d = datetime.utcnow() - timedelta(days=i)
            date_str = d.strftime('%Y-%m-%d')
            label = d.strftime('%a')  # Mon, Tue, etc.
            filled_daily.append({
                "date": date_str,
                "label": label,
                "count": daily_trends.get(date_str, 0)
            })
        filled_daily.reverse()

        # 4. Hourly activity spread (today)
        hourly_rows = conn.execute(
            """
            SELECT strftime('%H', timestamp) as hour, COUNT(*) as count
            FROM events
            WHERE timestamp >= datetime('now', 'start of day')
            GROUP BY hour
            ORDER BY hour ASC
            """
        ).fetchall()
        hourly = {int(row["hour"]): row["count"] for row in hourly_rows}
        hourly_filled = [{"hour": f"{h:02d}:00", "count": hourly.get(h, 0)} for h in range(24)]

        # 5. Weekly report summary (this week vs last week)
        this_week = conn.execute(
            """
            SELECT COUNT(*) as count FROM events
            WHERE timestamp >= datetime('now', '-7 days')
            """
        ).fetchone()["count"]

        last_week = conn.execute(
            """
            SELECT COUNT(*) as count FROM events
            WHERE timestamp >= datetime('now', '-14 days')
              AND timestamp < datetime('now', '-7 days')
            """
        ).fetchone()["count"]

        # Top blocked URLs this week
        top_urls_rows = conn.execute(
            """
            SELECT url, COUNT(*) as count FROM events
            WHERE timestamp >= datetime('now', '-7 days')
            GROUP BY url
            ORDER BY count DESC
            LIMIT 5
            """
        ).fetchall()
        top_urls = [{"url": row["url"], "count": row["count"]} for row in top_urls_rows]

        # 6. Recent Alerts (Latest 50 for live feed)
        recent_rows = conn.execute(
            """
            SELECT id, event_type, url, snippet, severity, timestamp
            FROM events
            ORDER BY timestamp DESC
            LIMIT 50
            """
        ).fetchall()

        recent_alerts = []
        for row in recent_rows:
            recent_alerts.append({
                "id": row["id"],
                "type": row["event_type"],
                "url": row["url"] or "",
                "snippet": row["snippet"] or "",
                "severity": row["severity"],
                "time": row["timestamp"]
            })

        # 7. Today's incident count
        today_count = conn.execute(
            "SELECT COUNT(*) as count FROM events WHERE timestamp >= datetime('now', 'start of day')"
        ).fetchone()["count"]

        # 8. Danger score (weighted count of high severity events last 24h)
        danger_rows = conn.execute(
            """
            SELECT severity, COUNT(*) as count FROM events
            WHERE timestamp >= datetime('now', '-1 day')
            GROUP BY severity
            """
        ).fetchall()
        danger_weights = {"high": 3, "medium": 1, "low": 0}
        raw_score = sum(danger_weights.get(r["severity"], 0) * r["count"] for r in danger_rows)
        danger_score = min(100, raw_score)  # cap at 100

        return {
            "summary": stats,
            "severity": severity_stats,
            "trends": filled_daily,
            "hourly": hourly_filled,
            "recent": recent_alerts,
            "total_incidents": sum(stats.values()),
            "today_count": today_count,
            "this_week": this_week,
            "last_week": last_week,
            "top_urls": top_urls,
            "danger_score": danger_score,
        }
    finally:
        conn.close()
