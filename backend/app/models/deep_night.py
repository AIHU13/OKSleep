"""深夜计划模型：每晚计划 + 任务清单（表格配置）。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

DEEP_NIGHT_PLANS_TABLE = "deep_night_plans"

DEEP_NIGHT_PLANS_DDL = """
CREATE TABLE IF NOT EXISTS deep_night_plans (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL,
    session_id   INTEGER,                 -- 关联的助眠会话（启动后写入）
    date         TEXT,                    -- 入睡日 YYYY-MM-DD
    status       TEXT    NOT NULL DEFAULT 'draft',   -- draft | active | done
    created_at   TEXT    NOT NULL,
    updated_at   TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_plans_user ON deep_night_plans (user_id, status);
"""

PLAN_TASKS_TABLE = "plan_tasks"

PLAN_TASKS_DDL = """
CREATE TABLE IF NOT EXISTS plan_tasks (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id      INTEGER NOT NULL,
    user_id      INTEGER NOT NULL,
    category     TEXT    NOT NULL,        -- daily | work
    task_type    TEXT    NOT NULL,        -- breakfast | remind | weekly_report | ppt
    title        TEXT    NOT NULL,
    params       TEXT    NOT NULL DEFAULT '{}',  -- JSON：workspace/spec_doc/deliver_at/note/topic
    created_at   TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_plan_tasks_plan ON plan_tasks (plan_id);
"""


@dataclass
class DeepNightPlan:
    id: int
    user_id: int
    session_id: Optional[int] = None
    date: Optional[str] = None
    status: str = "draft"
    created_at: str = ""
    updated_at: str = ""

    @staticmethod
    def from_row(row) -> "DeepNightPlan":
        return DeepNightPlan(
            id=row["id"],
            user_id=row["user_id"],
            session_id=row["session_id"],
            date=row["date"],
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


@dataclass
class PlanTask:
    id: int
    plan_id: int
    user_id: int
    category: str
    task_type: str
    title: str
    params: dict
    created_at: str = ""

    @staticmethod
    def from_row(row) -> "PlanTask":
        import json

        try:
            params = json.loads(row["params"] or "{}")
        except Exception:
            params = {}
        return PlanTask(
            id=row["id"],
            plan_id=row["plan_id"],
            user_id=row["user_id"],
            category=row["category"],
            task_type=row["task_type"],
            title=row["title"],
            params=params,
            created_at=row["created_at"],
        )
