"""
Deduplicação / idempotência.

"""

import sqlite3
from pathlib import Path


class DedupeStore:
    def __init__(self, db_path: str):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS processed_events (
                event_key   TEXT PRIMARY KEY,
                entity_id   TEXT NOT NULL,
                processed_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        self._conn.commit()

    @staticmethod
    def make_key(entity_id: str, notified_at: str) -> str:
        return f"{entity_id}|{notified_at}"

    def already_processed(self, event_key: str) -> bool:
        cur = self._conn.execute(
            "SELECT 1 FROM processed_events WHERE event_key = ?", (event_key,)
        )
        return cur.fetchone() is not None

    def mark_processed(self, event_key: str, entity_id: str) -> None:
        self._conn.execute(
            "INSERT OR IGNORE INTO processed_events (event_key, entity_id) VALUES (?, ?)",
            (event_key, entity_id),
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()