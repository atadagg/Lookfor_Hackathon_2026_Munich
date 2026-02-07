"""SQLite persistence layer and LangGraph checkpointer wiring.

This keeps things **very simple** and does two jobs:

1. Provide a SQLite-backed checkpointer for LangGraph using its built-in
   `SqliteSaver`.
2. Create two tiny tables for your own reporting needs:
   - `threads`  – one row per email / ticket thread, with status + state.
   - `messages` – one row per email/message in that thread.

You can grow this later (Postgres, more columns, etc.) without changing
the public `Checkpointer` interface.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

try:  # LangGraph optional import so tests don't explode without it
    from langgraph.checkpoint.sqlite import SqliteSaver
except Exception:  # pragma: no cover - handled gracefully at runtime
    SqliteSaver = None  # type: ignore[assignment]


def _utc_now_iso() -> str:
    """Return a simple UTC timestamp string."""

    # Example: "2026-02-06T12:34:56.789123Z"
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass
class ThreadRecord:
    """Minimal view of a thread row used by application code."""

    id: int
    external_thread_id: str
    status: str
    current_workflow: Optional[str]
    workflow_step: Optional[str]
    is_escalated: bool
    escalated_at: Optional[str]


class Checkpointer:
    """SQLite-backed persistence + LangGraph checkpointer helper.

    - Use `save_state` / `load_state` for your own high-level state.
    - Use `save_message` to append an email/message to a thread.
    - Use `langgraph_saver` when compiling LangGraph graphs:

        graph = build_shipping_graph()
        cp = Checkpointer()
        app = graph.compile(checkpointer=cp.langgraph_saver)
    """

    def __init__(self, db_path: str = "state.db") -> None:
        self.db_path = db_path
        # `check_same_thread=False` so FastAPI / asyncio can share the connection.
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

        # Optional LangGraph saver that writes into the same SQLite file.
        self._lg_saver: Optional[Any] = SqliteSaver(self.db_path) if SqliteSaver else None

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------
    def _init_schema(self) -> None:
        """Create tables if they don't exist yet.

        Everything lives in a single file-backed SQLite database.
        """

        cur = self._conn.cursor()

        # One row per external email / ticket thread.
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS threads (
                id                 INTEGER PRIMARY KEY AUTOINCREMENT,
                external_thread_id TEXT NOT NULL UNIQUE,

                -- optional metadata
                customer_email     TEXT,
                subject            TEXT,

                -- high-level status for dashboards
                status             TEXT NOT NULL DEFAULT 'open', -- open | escalated | closed

                current_workflow   TEXT,
                workflow_step      TEXT,
                is_escalated       INTEGER NOT NULL DEFAULT 0,
                escalated_at       TEXT,

                -- full serialized macro state (AgentState)
                state_json         TEXT NOT NULL,

                created_at         TEXT NOT NULL,
                updated_at         TEXT NOT NULL,
                last_message_at    TEXT
            )
            """
        )

        # One row per email / chat message.
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id       INTEGER NOT NULL
                                   REFERENCES threads(id) ON DELETE CASCADE,

                role            TEXT NOT NULL,   -- user | assistant | system
                content         TEXT NOT NULL,

                external_msg_id TEXT,
                direction       TEXT NOT NULL,   -- inbound | outbound

                attachments_json TEXT,           -- JSON array of {object_key, filename, content_type}

                created_at      TEXT NOT NULL
            )
            """
        )

        # Migration: add attachments_json if table existed before (SQLite has no IF NOT EXISTS for columns)
        try:
            cur.execute(
                "ALTER TABLE messages ADD COLUMN attachments_json TEXT"
            )
        except sqlite3.OperationalError as e:
            if "duplicate column" not in str(e).lower():
                raise

        self._conn.commit()

    # ------------------------------------------------------------------
    # Public API for your app
    # ------------------------------------------------------------------
    def save_state(self, conversation_id: str, state: Dict[str, Any]) -> None:
        """Upsert the thread row + snapshot of the latest AgentState.

        - `conversation_id` is your external thread / ticket id.
        - `state` is the macro AgentState (LangGraph-compatible dict).
        """

        now = _utc_now_iso()

        # Derive high-level status from the state dict.
        is_escalated = bool(state.get("is_escalated"))
        status = "escalated" if is_escalated else "open"

        escalated_at_val = state.get("escalated_at")
        if isinstance(escalated_at_val, datetime):
            escalated_at = escalated_at_val.isoformat() + "Z"
        else:
            escalated_at = escalated_at_val if escalated_at_val is not None else None

        current_workflow = state.get("current_workflow")
        workflow_step = state.get("workflow_step")

        # Optional metadata from the state.
        customer_info = state.get("customer_info") or {}
        customer_email = customer_info.get("email")
        subject = state.get("subject")  # keep this flexible for later

        state_json = json.dumps(state, default=str)

        cur = self._conn.cursor()
        cur.execute(
            """
            INSERT INTO threads (
                external_thread_id,
                customer_email,
                subject,
                status,
                current_workflow,
                workflow_step,
                is_escalated,
                escalated_at,
                state_json,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(external_thread_id) DO UPDATE SET
                customer_email   = excluded.customer_email,
                subject          = excluded.subject,
                status           = excluded.status,
                current_workflow = excluded.current_workflow,
                workflow_step    = excluded.workflow_step,
                is_escalated     = excluded.is_escalated,
                escalated_at     = excluded.escalated_at,
                state_json       = excluded.state_json,
                updated_at       = excluded.updated_at
            """,
            (
                conversation_id,
                customer_email,
                subject,
                status,
                current_workflow,
                workflow_step,
                int(is_escalated),
                escalated_at,
                state_json,
                now,
                now,
            ),
        )
        self._conn.commit()

    def load_state(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Return the last saved AgentState for a conversation, if any."""

        cur = self._conn.cursor()
        cur.execute(
            "SELECT state_json FROM threads WHERE external_thread_id = ?",
            (conversation_id,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        return json.loads(row["state_json"])

    def save_message(
        self,
        conversation_id: str,
        *,
        role: str,
        content: str,
        direction: str,
        external_msg_id: Optional[str] = None,
        attachments_json: Optional[str] = None,
    ) -> bool:
        """Append a message row and bump `last_message_at` on the thread.

        If the thread doesn't exist yet, a minimal one is created with
        an empty state dict.

        Returns ``True`` if the message was inserted, or ``False`` if an
        identical message (same thread, role, content, direction) already
        exists as the most recent entry -- i.e. it is a duplicate.
        """

        now = _utc_now_iso()
        cur = self._conn.cursor()

        # Ensure the thread exists.
        cur.execute(
            "SELECT id FROM threads WHERE external_thread_id = ?",
            (conversation_id,),
        )
        row = cur.fetchone()
        if row is None:
            empty_state = {}
            state_json = json.dumps(empty_state)
            cur.execute(
                """
                INSERT INTO threads (
                    external_thread_id,
                    status,
                    state_json,
                    created_at,
                    updated_at,
                    last_message_at
                )
                VALUES (?, 'open', ?, ?, ?, ?)
                """,
                (conversation_id, state_json, now, now, now),
            )
            thread_id = cur.lastrowid
        else:
            thread_id = int(row["id"])

            # --- Duplicate check: compare against the last message for
            #     this thread with the same role and direction. -----------
            cur.execute(
                """
                SELECT content
                FROM messages
                WHERE thread_id = ? AND role = ? AND direction = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (thread_id, role, direction),
            )
            last_row = cur.fetchone()
            if last_row is not None and last_row["content"] == content:
                # Exact duplicate of the most recent message -- skip.
                return False

            cur.execute(
                """
                UPDATE threads
                SET last_message_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (now, now, thread_id),
            )

        # Insert the message.
        cur.execute(
            """
            INSERT INTO messages (
                thread_id,
                role,
                content,
                external_msg_id,
                direction,
                attachments_json,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (thread_id, role, content, external_msg_id, direction, attachments_json or None, now),
        )

        self._conn.commit()
        return True

    def get_thread(self, conversation_id: str) -> Optional[ThreadRecord]:
        """Lightweight helper to inspect the latest status of a thread."""

        cur = self._conn.cursor()
        cur.execute(
            """
            SELECT
                id,
                external_thread_id,
                status,
                current_workflow,
                workflow_step,
                is_escalated,
                escalated_at
            FROM threads
            WHERE external_thread_id = ?
            """,
            (conversation_id,),
        )
        row = cur.fetchone()
        if row is None:
            return None

        return ThreadRecord(
            id=int(row["id"]),
            external_thread_id=str(row["external_thread_id"]),
            status=str(row["status"]),
            current_workflow=row["current_workflow"],
            workflow_step=row["workflow_step"],
            is_escalated=bool(row["is_escalated"]),
            escalated_at=row["escalated_at"],
        )

    def get_messages(self, conversation_id: str) -> list[Dict[str, Any]]:
        """Return all messages for a given external thread id, oldest first."""

        cur = self._conn.cursor()
        cur.execute(
            """
            SELECT
                m.role,
                m.content,
                m.direction,
                m.attachments_json,
                m.created_at
            FROM messages AS m
            JOIN threads AS t
              ON m.thread_id = t.id
            WHERE t.external_thread_id = ?
            ORDER BY m.id ASC
            """,
            (conversation_id,),
        )
        rows = cur.fetchall()
        result = []
        for row in rows:
            msg = {
                "role": row["role"],
                "content": row["content"],
                "direction": row["direction"],
                "created_at": row["created_at"],
            }
            att_raw = row["attachments_json"] if row["attachments_json"] is not None else None
            if att_raw:
                try:
                    msg["attachments"] = json.loads(att_raw)
                except (json.JSONDecodeError, TypeError):
                    msg["attachments"] = []
            else:
                msg["attachments"] = []
            result.append(msg)
        return result

    def list_threads(self) -> list[Dict[str, Any]]:
        """Return all threads, newest first, with basic metadata."""

        cur = self._conn.cursor()
        cur.execute(
            """
            SELECT
                external_thread_id,
                customer_email,
                subject,
                status,
                current_workflow,
                workflow_step,
                is_escalated,
                escalated_at,
                state_json,
                created_at,
                updated_at,
                last_message_at
            FROM threads
            ORDER BY updated_at DESC
            """
        )
        rows = cur.fetchall()
        results = []
        for row in rows:
            state = {}
            try:
                state = json.loads(row["state_json"]) if row["state_json"] else {}
            except Exception:
                pass
            customer_info = state.get("customer_info") or {}
            messages = state.get("messages") or []
            first_user_msg = ""
            for m in messages:
                if isinstance(m, dict) and m.get("role") == "user":
                    first_user_msg = m.get("content", "")
                    break

            results.append({
                "conversation_id": row["external_thread_id"],
                "customer_email": row["customer_email"] or customer_info.get("email", ""),
                "customer_name": "%s %s" % (
                    customer_info.get("first_name", ""),
                    customer_info.get("last_name", ""),
                ) if customer_info.get("first_name") else "",
                "status": row["status"],
                "current_workflow": row["current_workflow"],
                "workflow_step": row["workflow_step"],
                "is_escalated": bool(row["is_escalated"]),
                "routed_agent": state.get("routed_agent", ""),
                "intent": state.get("intent", ""),
                "first_message": first_user_msg[:120],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            })
        return results

    # ------------------------------------------------------------------
    # LangGraph integration
    # ------------------------------------------------------------------
    @property
    def langgraph_saver(self) -> Any:
        """Expose LangGraph's `SqliteSaver` instance.

        Use this when compiling a LangGraph graph:

            cp = Checkpointer()
            app = graph.compile(checkpointer=cp.langgraph_saver)
        """

        if self._lg_saver is None:
            raise RuntimeError(
                "LangGraph is not installed. Add `langgraph` to requirements.txt."
            )
        return self._lg_saver


__all__ = ["Checkpointer", "ThreadRecord"]
