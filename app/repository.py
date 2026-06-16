from __future__ import annotations

import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[1] / "ticket_triage.db"


class TriageRepository:
    def __init__(self) -> None:
        self._init_db()

    def _init_db(self) -> None:
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS triage_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id TEXT,
                category TEXT,
                confidence REAL,
                escalation_probability REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
        conn.close()

    def save_run(
        self,
        ticket_id: str,
        category: str,
        confidence: float,
        escalation_probability: float,
    ) -> None:
        conn = sqlite3.connect(DB_PATH)
        conn.execute(
            """
            INSERT INTO triage_runs(ticket_id, category, confidence, escalation_probability)
            VALUES (?, ?, ?, ?)
            """,
            (ticket_id, category, confidence, escalation_probability),
        )
        conn.commit()
        conn.close()
