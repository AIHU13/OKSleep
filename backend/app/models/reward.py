"""奖励记录：积分 / 连续打卡流水（历史数据保存，验收清单项）。"""
from __future__ import annotations

from dataclasses import dataclass

REWARD_TABLE = "reward_records"

REWARD_DDL = """
CREATE TABLE IF NOT EXISTS reward_records (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id     INTEGER NOT NULL,
    user_id        INTEGER NOT NULL,
    date           TEXT    NOT NULL,
    coins          INTEGER NOT NULL,
    streak_after   INTEGER NOT NULL,
    total_after    INTEGER NOT NULL,
    message        TEXT,
    created_at     TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_rewards_user ON reward_records (user_id, date);
"""


@dataclass
class RewardRecord:
    id: int
    session_id: int
    user_id: int
    date: str
    coins: int
    streak_after: int
    total_after: int
    message: Optional[str] = None
    created_at: str = ""

    @staticmethod
    def from_row(row) -> "RewardRecord":
        return RewardRecord(
            id=row["id"],
            session_id=row["session_id"],
            user_id=row["user_id"],
            date=row["date"],
            coins=row["coins"],
            streak_after=row["streak_after"],
            total_after=row["total_after"],
            message=row["message"],
            created_at=row["created_at"],
        )
