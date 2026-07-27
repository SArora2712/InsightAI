"""
InsightAI - Chat history persistence.

SQLite-backed storage for multiple saved conversations. Designed to be
UI-agnostic: this module has no Streamlit dependency, so the same
functions will serve the FastAPI frontend later without changes.
"""
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

DB_PATH = Path("data/history.db")


def _get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables if they don't exist. Safe to call on every app startup."""
    conn = _get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            meta_json TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id)
        )
    """)
    conn.commit()
    conn.close()


def create_conversation(title: str = "New conversation") -> str:
    conv_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    conn = _get_connection()
    conn.execute(
        "INSERT INTO conversations (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
        (conv_id, title, now, now),
    )
    conn.commit()
    conn.close()
    return conv_id


def save_message(conversation_id: str, role: str, content: str, meta: Optional[dict] = None) -> None:
    if content is None:
         raise ValueError(
            f"save_message() received None content. "
            f"role={role}, conversation_id={conversation_id}"
        )

    
    if not isinstance(content, str):
        content = str(content)   

    msg_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    meta_json = json.dumps(meta, default=str) if meta else None

    conn = _get_connection()
    try:

        conn.execute(
        "INSERT INTO messages (id, conversation_id, role, content, meta_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (msg_id, conversation_id, role, content, meta_json, now),
        )
        conn.execute(
        "UPDATE conversations SET updated_at = ? WHERE id = ?",
        (now, conversation_id),
        )
        conn.commit()
    finally:
        conn.close()


def maybe_set_title_from_first_message(conversation_id: str, first_user_message: str) -> None:
    """Auto-titles a conversation from its first message, truncated. Only
    applies if the conversation still has its default placeholder title."""
    conn = _get_connection()
    row = conn.execute("SELECT title FROM conversations WHERE id = ?", (conversation_id,)).fetchone()
    if row and row["title"] == "New conversation":
        title = first_user_message.strip()[:60]
        if len(first_user_message.strip()) > 60:
            title += "..."
        conn.execute("UPDATE conversations SET title = ? WHERE id = ?", (title, conversation_id))
        conn.commit()
    conn.close()


def list_conversations(limit: int = 50) -> list[dict]:
    conn = _get_connection()
    rows = conn.execute(
        "SELECT id, title, created_at, updated_at FROM conversations ORDER BY updated_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def load_conversation_messages(conversation_id: str) -> list[dict]:
    conn = _get_connection()
    rows = conn.execute(
        "SELECT role, content, meta_json FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
        (conversation_id,),
    ).fetchall()
    conn.close()
    return [
        {
            "role": row["role"],
            "content": row["content"],
            "meta": json.loads(row["meta_json"]) if row["meta_json"] else None,
        }
        for row in rows
    ]


def delete_conversation(conversation_id: str) -> None:
    conn = _get_connection()
    conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
    conn.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
    conn.commit()
    conn.close()

def rename_conversation(conversation_id: str, new_title: str) -> None:
    conn = _get_connection()
    conn.execute(
        "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
        (new_title, datetime.now(timezone.utc).isoformat(), conversation_id),
    )
    conn.commit()
    conn.close()