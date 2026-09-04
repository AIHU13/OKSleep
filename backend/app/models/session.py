"""睡前会话（Session）：后端维护核心业务状态（规范第 10/11 条）。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

SLEEP_SESSION_TABLE = "sleep_sessions"

SLEEP_SESSION_DDL = """
CREATE TABLE IF NOT EXISTS sleep_sessions (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id           INTEGER NOT NULL,
    date              TEXT    NOT NULL,
    state             TEXT    NOT NULL,
    stage             INTEGER,
    scenario          TEXT,
    content_id        INTEGER,
    content_type      TEXT,
    started_at        TEXT    NOT NULL,
    sleep_started_at  TEXT,
    updated_at        TEXT    NOT NULL,
    created_at        TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sleep_sessions (user_id, state);
"""


@dataclass
class SleepSession:
    id: int
    user_id: int
    date: str
    state: str
    stage: Optional[int] = None
    scenario: Optional[str] = None
    content_id: Optional[int] = None
    content_type: Optional[str] = None
    started_at: str = ""
    sleep_started_at: Optional[str] = None
    updated_at: str = ""
    created_at: str = ""

    @staticmethod
    def from_row(row) -> "SleepSession":
        return SleepSession(
            id=row["id"],
            user_id=row["user_id"],
            date=row["date"],
            state=row["state"],
            stage=row["stage"],
            scenario=row["scenario"],
            content_id=row["content_id"],
            content_type=row["content_type"],
            started_at=row["started_at"],
            sleep_started_at=row["sleep_started_at"],
            updated_at=row["updated_at"],
            created_at=row["created_at"],
        )
