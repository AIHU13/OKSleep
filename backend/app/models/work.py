"""工作型/服务型 Agent 任务与外卖订单表。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

WORK_TASKS_TABLE = "work_tasks"

WORK_TASKS_DDL = """
CREATE TABLE IF NOT EXISTS work_tasks (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL,
    session_id    INTEGER NOT NULL,
    kind          TEXT    NOT NULL,
    name          TEXT    NOT NULL,
    icon          TEXT,
    duration_min  INTEGER NOT NULL,
    created_at    TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_work_tasks_session ON work_tasks (session_id);
"""

FOOD_ORDERS_TABLE = "food_orders"

FOOD_ORDERS_DDL = """
CREATE TABLE IF NOT EXISTS food_orders (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    source      TEXT    NOT NULL,            -- redeem_breakfast | work_agent
    item_name   TEXT    NOT NULL,
    note        TEXT,
    placed_at   TEXT    NOT NULL,
    created_at  TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_food_orders_user ON food_orders (user_id, id);
"""


@dataclass
class WorkTask:
    id: int
    user_id: int
    session_id: int
    kind: str
    name: str
    icon: Optional[str] = None
    duration_min: int = 6
    created_at: str = ""

    @staticmethod
    def from_row(row) -> "WorkTask":
        return WorkTask(
            id=row["id"],
            user_id=row["user_id"],
            session_id=row["session_id"],
            kind=row["kind"],
            name=row["name"],
            icon=row["icon"],
            duration_min=row["duration_min"],
            created_at=row["created_at"],
        )


@dataclass
class FoodOrder:
    id: int
    user_id: int
    source: str
    item_name: str
    note: Optional[str] = None
    placed_at: str = ""
    created_at: str = ""

    @staticmethod
    def from_row(row) -> "FoodOrder":
        return FoodOrder(
            id=row["id"],
            user_id=row["user_id"],
            source=row["source"],
            item_name=row["item_name"],
            note=row["note"],
            placed_at=row["placed_at"],
            created_at=row["created_at"],
        )
