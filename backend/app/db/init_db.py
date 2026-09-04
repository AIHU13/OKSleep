"""建库与种子数据。"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from ..clock import fmt, now_dt
from ..config import DEFAULT_DB_PATH
from ..models.deep_night import DEEP_NIGHT_PLANS_DDL, DEEP_NIGHT_PLANS_TABLE, PLAN_TASKS_DDL, PLAN_TASKS_TABLE
from ..models.intervention import INTERVENTION_DDL, INTERVENTION_TABLE
from ..models.miss import MISS_DDL, MISS_TABLE
from ..models.reward import REWARD_DDL, REWARD_TABLE
from ..models.session import SLEEP_SESSION_DDL, SLEEP_SESSION_TABLE
from ..models.shop import SHOP_ORDER_DDL, SHOP_ORDER_TABLE
from ..models.user import USER_PROFILE_DDL, USER_PROFILE_TABLE
from ..models.work import FOOD_ORDERS_DDL, FOOD_ORDERS_TABLE, WORK_TASKS_DDL, WORK_TASKS_TABLE
from .database import connect

META_FLAGS_DDL = """
CREATE TABLE IF NOT EXISTS meta_flags (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

DEMO_STATE_DDL = """
CREATE TABLE IF NOT EXISTS demo_state (
    id           INTEGER PRIMARY KEY,
    virtual_now  TEXT,
    updated_at   TEXT
);
"""

ALL_DDL: list[str] = [
    USER_PROFILE_DDL,
    SLEEP_SESSION_DDL,
    INTERVENTION_DDL,
    REWARD_DDL,
    MISS_DDL,
    SHOP_ORDER_DDL,
    WORK_TASKS_DDL,
    FOOD_ORDERS_DDL,
    DEEP_NIGHT_PLANS_DDL,
    PLAN_TASKS_DDL,
    DEMO_STATE_DDL,
    META_FLAGS_DDL,
]

# 默认用户画像（设计说明 §3.1：23:30 / 07:30 / 偏好 音乐+故事）
DEFAULT_USER_JSON = {
    "weekday_bedtime": "23:30",
    "weekday_wake": "07:30",
    "weekend_bedtime": "23:30",
    "weekend_wake": "07:30",
    "preferred_content": '["music","story"]',
}


def init_db(db_path: Path | str | None = None) -> sqlite3.Connection:
    """建表 + 种子数据；幂等，可重复调用。"""
    conn = connect(db_path)
    try:
        for ddl in ALL_DDL:
            # DDL 中包含多语句（建表 + 索引），必须使用 executescript
            conn.executescript(ddl)
        conn.commit()

        _seed_user(conn)
        _seed_demo_state(conn)
        _seed_meta(conn)
        conn.commit()
        return conn
    except Exception:
        conn.close()
        raise


def _seed_user(conn: sqlite3.Connection) -> None:
    row = conn.execute(f"SELECT id FROM {USER_PROFILE_TABLE} WHERE id = 1").fetchone()
    if row:
        return
    conn.execute(
        f"""INSERT INTO {USER_PROFILE_TABLE}
            (id, weekday_bedtime, weekday_wake, weekend_bedtime, weekend_wake,
             preferred_content, streak_days, total_coins, last_success_date, created_at)
            VALUES (1, :weekday_bedtime, :weekday_wake, :weekend_bedtime, :weekend_wake,
                    :preferred_content, 0, 0, NULL, :created_at)""",
        {**DEFAULT_USER_JSON, "created_at": fmt(now_dt())},
    )


def _seed_demo_state(conn: sqlite3.Connection) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO demo_state (id, virtual_now, updated_at) VALUES (1, NULL, NULL)"
    )


def _seed_meta(conn: sqlite3.Connection) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO meta_flags (key, value) VALUES ('onboarding_done', '0')"
    )


def ensure_initialized(db_path: Path | str | None = None) -> sqlite3.Connection:
    """供应用启动时调用：若库文件不存在则初始化。"""
    path = Path(db_path) if db_path else DEFAULT_DB_PATH
    if not path.exists():
        init_db(path)
    return connect(path)


def reset_demo_state(conn: sqlite3.Connection) -> None:
    """清空演示数据（重置 Demo 用）：清 session/intervention/reward/订单 与虚拟时间。"""
    for table in (
        MISS_TABLE,
        PLAN_TASKS_TABLE,
        DEEP_NIGHT_PLANS_TABLE,
        FOOD_ORDERS_TABLE,
        WORK_TASKS_TABLE,
        SHOP_ORDER_TABLE,
        REWARD_TABLE,
        INTERVENTION_TABLE,
        SLEEP_SESSION_TABLE,
    ):
        conn.execute(f"DELETE FROM {table}")
    conn.execute("UPDATE demo_state SET virtual_now = NULL, updated_at = ? WHERE id = 1",
                 (fmt(now_dt()),))
    conn.execute(
        f"UPDATE {USER_PROFILE_TABLE} SET streak_days = 0, total_coins = 0, "
        f"last_success_date = NULL WHERE id = 1"
    )
    conn.execute(
        "UPDATE meta_flags SET value = '0' WHERE key = 'onboarding_done'"
    )
    conn.commit()
