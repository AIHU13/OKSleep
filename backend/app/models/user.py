"""用户作息画像。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

USER_PROFILE_TABLE = "user_profile"

USER_PROFILE_DDL = """
CREATE TABLE IF NOT EXISTS user_profile (
    id                  INTEGER PRIMARY KEY,
    weekday_bedtime     TEXT    NOT NULL DEFAULT '23:30',
    weekday_wake        TEXT    NOT NULL DEFAULT '07:30',
    weekend_bedtime     TEXT    NOT NULL DEFAULT '23:30',
    weekend_wake        TEXT    NOT NULL DEFAULT '07:30',
    preferred_content   TEXT    NOT NULL DEFAULT '["music","story"]',
    streak_days         INTEGER NOT NULL DEFAULT 0,
    total_coins         INTEGER NOT NULL DEFAULT 0,
    last_success_date   TEXT,
    created_at          TEXT    NOT NULL
)
"""


@dataclass
class UserProfile:
    id: int
    weekday_bedtime: str
    weekday_wake: str
    weekend_bedtime: str
    weekend_wake: str
    preferred_content: list[str] = field(default_factory=lambda: ["music", "story"])
    streak_days: int = 0
    total_coins: int = 0
    last_success_date: Optional[str] = None
    created_at: str = ""

    @property
    def is_empty(self) -> bool:
        return False

    @staticmethod
    def from_row(row) -> "UserProfile":
        import json

        return UserProfile(
            id=row["id"],
            weekday_bedtime=row["weekday_bedtime"],
            weekday_wake=row["weekday_wake"],
            weekend_bedtime=row["weekend_bedtime"],
            weekend_wake=row["weekend_wake"],
            preferred_content=json.loads(row["preferred_content"] or '["music","story"]'),
            streak_days=row["streak_days"],
            total_coins=row["total_coins"],
            last_success_date=row["last_success_date"],
            created_at=row["created_at"],
        )
