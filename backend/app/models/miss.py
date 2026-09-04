"""助眠失败记录（模拟未按时进入睡眠，用于睡眠记录与积分扣减展示）。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

MISS_TABLE = "miss_records"

MISS_DDL = """
CREATE TABLE IF NOT EXISTS miss_records (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    date            TEXT    NOT NULL,
    scenario        TEXT,
    coins_deducted  INTEGER NOT NULL DEFAULT 0,
    message         TEXT,
    created_at      TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_miss_user ON miss_records (user_id, id);
"""


@dataclass
class MissRecord:
    id: int
    user_id: int
    date: str
    scenario: Optional[str] = None
    coins_deducted: int = 0
    message: Optional[str] = None
    created_at: str = ""

    @staticmethod
    def from_row(row) -> "MissRecord":
        return MissRecord(
            id=row["id"],
            user_id=row["user_id"],
            date=row["date"],
            scenario=row["scenario"],
            coins_deducted=row["coins_deducted"],
            message=row["message"],
            created_at=row["created_at"],
        )
