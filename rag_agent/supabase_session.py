"""Supabase-backed implementation of the OpenAI Agents SDK Session protocol."""

from __future__ import annotations

import json
import logging
from typing import Any

from supabase import Client
from agents.memory.session import Session
from agents.memory.session_settings import SessionSettings, resolve_session_limit
from agents.items import TResponseInputItem

logger = logging.getLogger(__name__)

SESSIONS_TABLE = "agent_sessions"
MESSAGES_TABLE = "agent_messages"


class SupabaseSession:
    """Supabase-backed session storage.

    Stores conversation history in two Supabase tables:
    - ``agent_sessions`` — session metadata (session_id, timestamps).
    - ``agent_messages`` — individual message items as JSONB rows.

    Implements the ``Session`` protocol expected by ``Runner.run(session=...)``.
    """

    def __init__(
        self,
        session_id: str,
        supabase: Client,
        session_settings: SessionSettings | None = None,
    ):
        self.session_id = session_id
        self.supabase = supabase
        self.session_settings = session_settings or SessionSettings()

    # ------------------------------------------------------------------
    # Session protocol methods
    # ------------------------------------------------------------------

    async def get_items(self, limit: int | None = None) -> list[TResponseInputItem]:
        """Retrieve conversation history for this session."""
        session_limit = resolve_session_limit(limit, self.session_settings)

        try:
            query = (
                self.supabase.table(MESSAGES_TABLE)
                .select("message_data")
                .eq("session_id", self.session_id)
                .order("id", desc=False)
            )

            if session_limit is not None:
                # Fetch the latest N items: order DESC, limit, then reverse
                query = (
                    self.supabase.table(MESSAGES_TABLE)
                    .select("message_data")
                    .eq("session_id", self.session_id)
                    .order("id", desc=True)
                    .limit(session_limit)
                )
                response = query.execute()
                rows = list(reversed(response.data or []))
            else:
                response = query.execute()
                rows = response.data or []

            items: list[TResponseInputItem] = []
            for row in rows:
                data = row["message_data"]
                # Supabase returns JSONB as parsed dicts already
                if isinstance(data, str):
                    try:
                        data = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                items.append(data)

            return items

        except Exception:
            logger.exception("supabase_session.get_items failed for session=%s", self.session_id)
            return []

    async def add_items(self, items: list[TResponseInputItem]) -> None:
        """Add new items to the conversation history."""
        if not items:
            return

        try:
            # Ensure session row exists
            self.supabase.table(SESSIONS_TABLE).upsert(
                {"session_id": self.session_id},
                on_conflict="session_id",
            ).execute()

            # Insert message rows
            rows = [
                {
                    "session_id": self.session_id,
                    "message_data": json.dumps(item) if not isinstance(item, str) else item,
                }
                for item in items
            ]
            self.supabase.table(MESSAGES_TABLE).insert(rows).execute()

            # Touch updated_at
            self.supabase.table(SESSIONS_TABLE).update(
                {"updated_at": "now()"}
            ).eq("session_id", self.session_id).execute()

        except Exception:
            logger.exception("supabase_session.add_items failed for session=%s", self.session_id)

    async def pop_item(self) -> TResponseInputItem | None:
        """Remove and return the most recent item from the session."""
        try:
            # Fetch the last message
            response = (
                self.supabase.table(MESSAGES_TABLE)
                .select("id, message_data")
                .eq("session_id", self.session_id)
                .order("id", desc=True)
                .limit(1)
                .execute()
            )

            rows = response.data or []
            if not rows:
                return None

            row = rows[0]
            row_id = row["id"]

            # Delete it
            self.supabase.table(MESSAGES_TABLE).delete().eq("id", row_id).execute()

            data = row["message_data"]
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except json.JSONDecodeError:
                    return None
            return data

        except Exception:
            logger.exception("supabase_session.pop_item failed for session=%s", self.session_id)
            return None

    async def clear_session(self) -> None:
        """Clear all items for this session."""
        try:
            self.supabase.table(MESSAGES_TABLE).delete().eq(
                "session_id", self.session_id
            ).execute()
            self.supabase.table(SESSIONS_TABLE).delete().eq(
                "session_id", self.session_id
            ).execute()
        except Exception:
            logger.exception(
                "supabase_session.clear_session failed for session=%s", self.session_id
            )
