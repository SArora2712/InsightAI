"""
InsightAI - Safe, read-only SQL execution against the Northwind SQLite database.
"""
import sqlite3
import time
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "db" / "northwind.db"
QUERY_TIMEOUT_SECONDS = 10

# Small TTL cache: SQL results are deterministic and expensive; caching them
# for ~60s stops the dashboard / simulator / report from re-hitting the DB on
# every rerun or repeated request. Keyed by DB path + SQL + params.
_SQL_CACHE: dict = {}
_SQL_CACHE_TTL_SECONDS = 60
_SQL_CACHE_MAX_ENTRIES = 256


class SQLExecutionError(Exception):
    pass


def execute_sql(sql: str, db_path: Path = DB_PATH, params: tuple | None = None) -> dict:
   
    cache_key = (str(db_path), sql, params)
    now = time.time()
    cached = _SQL_CACHE.get(cache_key)
    if cached is not None and now - cached[0] < _SQL_CACHE_TTL_SECONDS:
        return cached[1]

    uri = f"file:{db_path}?mode=ro"
    start = time.time()
    try:
        conn = sqlite3.connect(uri, uri=True, timeout=QUERY_TIMEOUT_SECONDS)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(sql, params) if params is not None else cur.execute(sql)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description] if cur.description else []
        conn.close()
    except sqlite3.Error as e:
        raise SQLExecutionError(str(e)) from e

    elapsed_ms = round((time.time() - start) * 1000, 1)
    result = {
        "columns": columns,
        "rows": [dict(row) for row in rows],
        "row_count": len(rows),
        "execution_time_ms": elapsed_ms,
    }

    _SQL_CACHE[cache_key] = (now, result)
    if len(_SQL_CACHE) > _SQL_CACHE_MAX_ENTRIES:
        for k in [k for k, (ts, _) in _SQL_CACHE.items() if now - ts >= _SQL_CACHE_TTL_SECONDS]:
            _SQL_CACHE.pop(k, None)

    return result

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

