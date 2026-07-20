"""
InsightAI - Safe, read-only SQL execution against the Northwind SQLite database.
"""
import sqlite3
import time
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "db" / "northwind.db"
QUERY_TIMEOUT_SECONDS = 10


class SQLExecutionError(Exception):
    pass


def execute_sql(sql: str, db_path: Path = DB_PATH) -> dict:
   
    uri = f"file:{db_path}?mode=ro"
    start = time.time()
    try:
        conn = sqlite3.connect(uri, uri=True, timeout=QUERY_TIMEOUT_SECONDS)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description] if cur.description else []
        conn.close()
    except sqlite3.Error as e:
        raise SQLExecutionError(str(e)) from e

    elapsed_ms = round((time.time() - start) * 1000, 1)
    return {
        "columns": columns,
        "rows": [dict(row) for row in rows],
        "row_count": len(rows),
        "execution_time_ms": elapsed_ms,
    }

def get_max_order_date(db_path: Path = DB_PATH) -> str | None:
    
    uri = f"file:{db_path}?mode=ro"
    try:
        conn = sqlite3.connect(uri, uri=True)
        cur = conn.cursor()
        cur.execute("SELECT MAX(OrderDate) FROM Orders")
        result = cur.fetchone()
        conn.close()
        return result[0] if result else None
    except sqlite3.Error:
        return None