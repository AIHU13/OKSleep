"""干预记录：每次 AI/规则提醒落库，作为历史与个性化依据。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

INTERVENTION_TABLE = "interventions"

INTERVENTION_DDL = """
CREATE TABLE IF NOT EXISTS interventions (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id   INTEGER NOT NULL,
    state        TEXT    NOT NULL,
    stage        INTEGER,
    action       TEXT,
    scenario     TEXT,
    source       TEXT    NOT NULL DEFAULT 'mock',
    text         TEXT    NOT NULL,
    suggestion   TEXT,
    created_at   TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_interventions_session ON interventions (session_id);
"""


@dataclass
class Intervention:
    id: int
    session_id: int
    state: str
    stage: Optional[int] = None
    action: Optional[str] = None
    scenario: Optional[str] = None
    source: str = "mock"
    text: str = ""
    suggestion: Optional[str] = None
    created_at: str = ""

    @staticmethod
    def from_row(row) -> "Intervention":
        return Intervention(
            id=row["id"],
            session_id=row["session_id"],
            state=row["state"],
            stage=row["stage"],
            action=row["action"],
            scenario=row["scenario"],
            source=row["source"],
            text=row["text"],
            suggestion=row["suggestion"],
            created_at=row["created_at"],
        )
