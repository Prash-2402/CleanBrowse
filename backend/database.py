import sqlite3
from datetime import datetime

from backend.api_config import DATABASE_PATH

def get_db_connection() -> sqlite3.Connection:
    """Gets a connection to the SQLite local database."""
    # Ensure parents directories exist if needed
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(DATABASE_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    """Initializes the events table inside SQLite."""
    conn = get_db_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                url TEXT,
                snippet TEXT,
                severity TEXT DEFAULT 'medium',
                timestamp DATETIME NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()

def insert_event(event_type: str, url: str, snippet: str = "", severity: str = "medium") -> int:
    """Helper to insert an event and return its recorded ID. Snippets are truncated to 250 characters."""
    truncated_snippet = str(snippet)[:250] if snippet else ""
    
    conn = get_db_connection()
    try:
        cursor = conn.execute(
            """
            INSERT INTO events (event_type, url, snippet, severity, timestamp)
            VALUES (?, ?, ?, ?, ?)
            """,
            (event_type, url, truncated_snippet, severity, datetime.utcnow())
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()
