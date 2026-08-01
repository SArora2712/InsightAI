"""
InsightAI - Chat history persistence.

SQLite-backed storage for multiple saved conversations.
UI-agnostic: this module has zero Streamlit dependency.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

DB_PATH = Path("data/history.db")


def _get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    # Enforce foreign keys (important for cascading deletes later if needed)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """Create / upgrade tables. Safe to call on every app startup."""
    conn = _get_connection()
    try:
        # Create tables if they don't exist
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id          TEXT PRIMARY KEY,
                title       TEXT NOT NULL,
                created_at  TEXT NOT NULL,
                updated_at  TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id               TEXT PRIMARY KEY,
                conversation_id  TEXT NOT NULL,
                role             TEXT NOT NULL,
                content          TEXT NOT NULL,
                meta_json        TEXT,
                created_at       TEXT NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            )
        """)

        # --- Schema migration for older databases ---
        # Add meta_json column if it is missing
        columns = [row[1] for row in conn.execute("PRAGMA table_info(messages)").fetchall()]
        if "meta_json" not in columns:
            conn.execute("ALTER TABLE messages ADD COLUMN meta_json TEXT")

        # Indexes
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_conversation_id
            ON messages(conversation_id)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversations_updated_at
            ON conversations(updated_at DESC)
        """)

        conn.commit()
    finally:
        conn.close()

def create_conversation(title: str = "New conversation") -> str:
    """Create a new empty conversation and return its id."""
    conv_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    conn = _get_connection()
    try:
        conn.execute(
            "INSERT INTO conversations (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (conv_id, title, now, now),
        )
        conn.commit()
    finally:
        conn.close()
    return conv_id


def save_message(
    conversation_id: str,
    role: str,
    content: str,
    meta: Optional[dict] = None,
) -> None:
    """Persist a single message and bump the conversation's updated_at."""
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
            """
            INSERT INTO messages
                (id, conversation_id, role, content, meta_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (msg_id, conversation_id, role, content, meta_json, now),
        )
        conn.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (now, conversation_id),
        )
        conn.commit()
    finally:
        conn.close()


def maybe_set_title_from_first_message(
    conversation_id: str, first_user_message: str
) -> None:
    """Auto-title a conversation from its first user message (only if still 'New conversation')."""
    if not first_user_message or not first_user_message.strip():
        return

    title = first_user_message.strip()[:60]
    if len(first_user_message.strip()) > 60:
        title += "..."

    conn = _get_connection()
    try:
        row = conn.execute(
            "SELECT title FROM conversations WHERE id = ?", (conversation_id,)
        ).fetchone()
        if row and row["title"] == "New conversation":
            conn.execute(
                "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
                (title, datetime.now(timezone.utc).isoformat(), conversation_id),
            )
            conn.commit()
    finally:
        conn.close()


def list_conversations(
    limit: int = 50, only_with_messages: bool = True
) -> list[dict]:
    """
    Return conversations ordered by most recently updated.
    By default only returns conversations that actually contain messages
    (prevents empty 'New conversation' entries from cluttering the sidebar).
    """
    conn = _get_connection()
    try:
        if only_with_messages:
            rows = conn.execute(
                """
                SELECT c.id, c.title, c.created_at, c.updated_at
                FROM conversations c
                WHERE EXISTS (
                    SELECT 1 FROM messages m WHERE m.conversation_id = c.id
                )
                ORDER BY c.updated_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, title, created_at, updated_at
                FROM conversations
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def load_conversation_messages(conversation_id: str) -> list[dict]:
    """Return all messages for a conversation in chronological order."""
    conn = _get_connection()
    try:
        rows = conn.execute(
            """
            SELECT role, content, meta_json, created_at
            FROM messages
            WHERE conversation_id = ?
            ORDER BY created_at ASC
            """,
            (conversation_id,),
        ).fetchall()

        result = []
        for row in rows:
            # Safe meta parsing
            meta = None
            meta_raw = row["meta_json"] if row["meta_json"] is not None else None
            if meta_raw:
                try:
                    meta = json.loads(meta_raw)
                except (json.JSONDecodeError, TypeError):
                    meta = None

            result.append({
                "role": row["role"],
                "content": row["content"],
                "meta": meta,
                "created_at": row["created_at"],   # ← always include it
            })
        return result
    finally:
        conn.close()

def delete_conversation(conversation_id: str) -> None:
    """Delete a conversation and all its messages."""
    conn = _get_connection()
    try:
        # Order matters if foreign keys are not cascading, but we enabled CASCADE
        conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
        conn.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
        conn.commit()
    finally:
        conn.close()


def rename_conversation(conversation_id: str, new_title: str) -> None:
    """Rename a conversation."""
    new_title = (new_title or "").strip()
    if not new_title:
        return

    conn = _get_connection()
    try:
        conn.execute(
            """
            UPDATE conversations
            SET title = ?, updated_at = ?
            WHERE id = ?
            """,
            (new_title, datetime.now(timezone.utc).isoformat(), conversation_id),
        )
        conn.commit()
    finally:
        conn.close()


def get_conversation(conversation_id: str) -> Optional[dict]:
    """Fetch a single conversation by id (handy for future features)."""
    conn = _get_connection()
    try:
        row = conn.execute(
            "SELECT id, title, created_at, updated_at FROM conversations WHERE id = ?",
            (conversation_id,),
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()