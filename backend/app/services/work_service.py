"""深夜计划服务：工作 Agent 任务（模拟规划与自主执行）+ 早餐外卖下单。

说明：当前为 Mock 自主执行（任务随 Demo 虚拟时间自动推进），
接口已预留为后续对接真实工作型 Agent（数据汇总 / 报告整理 / PPT 生成）与服务型 Agent（外卖）。
"""
from __future__ import annotations

import sqlite3

from ..agent import state as sm
from ..clock import effective_now, fmt, parse_dt
from ..config import settings
from ..db.database import execute, query_all, query_one
from ..mock.work import (
    FOOD_STAGE_AT_MIN,
    FOOD_STAGES,
    FOOD_TOTAL_MIN,
    TASK_KEY_TO_TYPE,
    WORK_TASK_TYPES,
)
from ..models.session import SLEEP_SESSION_TABLE
from ..models.work import FOOD_ORDERS_TABLE, WORK_TASKS_TABLE
from .errors import RuleError


# --------------------------------------------------------------------------
# 工作 Agent 任务
# --------------------------------------------------------------------------

def task_types() -> list[dict]:
    return [dict(t) for t in WORK_TASK_TYPES]


def _require_work_stage(conn: sqlite3.Connection, session_id: int) -> sqlite3.Row:
    """规则：深夜计划仅开放给「加班场景且进入 Stage 3」的会话。"""
    row = query_one(
        conn,
        f"SELECT id, scenario, state FROM {SLEEP_SESSION_TABLE} WHERE id = ? AND user_id = ?",
        (session_id, settings.demo_user_id),
    )
    if not row:
        raise RuleError("会话不存在", code="session_not_found", http_status=404)
    if row["scenario"] != "working":
        raise RuleError("深夜计划仅对「仍在工作/加班」场景开放", code="not_working_scenario")
    if row["state"] != sm.STATE_STAGE_3:
        raise RuleError("深夜计划需先进入干预的第三阶段", code="not_stage3")
    return row


def start_work_task(
    conn: sqlite3.Connection, kind: str, session_id: int | None = None
) -> dict:
    task = TASK_KEY_TO_TYPE.get(kind)
    if not task:
        raise RuleError("未知的工作任务类型", code="bad_task", http_status=422)

    if session_id is None:
        from .session_service import active_session

        sess = active_session(conn)
        session_id = sess.id if sess else None
    if not session_id:
        raise RuleError("没有进行中的会话", code="no_session", http_status=404)
    _require_work_stage(conn, session_id)

    tid = execute(
        conn,
        f"""INSERT INTO {WORK_TASKS_TABLE}
            (user_id, session_id, kind, name, icon, duration_min, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            settings.demo_user_id,
            session_id,
            task["key"],
            task["name"],
            task["icon"],
            task["duration_min"],
            fmt(effective_now(conn)),  # 与虚拟时钟同一时间域，便于 Demo 推进
        ),
    )
    row = query_one(conn, f"SELECT * FROM {WORK_TASKS_TABLE} WHERE id = ?", (tid,))
    return _task_out(conn, row)


def tasks(conn: sqlite3.Connection, session_id: int) -> list[dict]:
    rows = query_all(
        conn,
        f"SELECT * FROM {WORK_TASKS_TABLE} WHERE user_id = ? AND session_id = ? "
        f"ORDER BY id DESC LIMIT 10",
        (settings.demo_user_id, session_id),
    )
    return [_task_out(conn, row) for row in rows]


def _task_out(conn: sqlite3.Connection, row: sqlite3.Row) -> dict:
    """任务进度由虚拟时间推算（Mock 自主执行）：queued -> running -> done。"""
    created = parse_dt(row["created_at"])
    elapsed_min = max(0, (effective_now(conn) - created).total_seconds() // 60)
    duration = int(row["duration_min"])
    progress = min(100, int(elapsed_min / duration * 100))
    if progress >= 100:
        status = "done"
        result = TASK_KEY_TO_TYPE.get(row["kind"], {}).get("result", "任务已完成 ✅")
    elif progress > 0:
        status = "running"
        result = None
    else:
        status = "queued"
        result = None
    return {
        "id": row["id"],
        "kind": row["kind"],
        "name": row["name"],
        "icon": row["icon"],
        "status": status,
        "progress": progress,
        "result": result,
        "created_at": row["created_at"],
    }


# --------------------------------------------------------------------------
# 早餐外卖（服务 Agent）
# --------------------------------------------------------------------------

def place_food_order(
    conn: sqlite3.Connection,
    source: str,
    note: str | None = None,
    item_name: str | None = None,
) -> dict:
    if source not in ("redeem_breakfast", "work_agent"):
        raise RuleError("未知的外卖来源", code="bad_source", http_status=422)
    from ..mock.work import BREAKFAST_ITEM

    name = item_name or BREAKFAST_ITEM["item_name"]
    now = effective_now(conn)  # 与虚拟时钟同一时间域
    oid = execute(
        conn,
        f"""INSERT INTO {FOOD_ORDERS_TABLE}
            (user_id, source, item_name, note, placed_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?)""",
        (settings.demo_user_id, source, name, note or None, fmt(now), fmt(now)),
    )
    row = query_one(conn, f"SELECT * FROM {FOOD_ORDERS_TABLE} WHERE id = ?", (oid,))
    return _food_out(conn, row)


def food_orders(conn: sqlite3.Connection, limit: int = 5) -> list[dict]:
    rows = query_all(
        conn,
        f"SELECT * FROM {FOOD_ORDERS_TABLE} WHERE user_id = ? ORDER BY id DESC LIMIT ?",
        (settings.demo_user_id, int(limit)),
    )
    return [_food_out(conn, row) for row in rows]


def _food_out(conn: sqlite3.Connection, row: sqlite3.Row) -> dict:
    """配送进度同样由虚拟时间推算（下单后 13 分钟送达）。"""
    placed = parse_dt(row["placed_at"])
    elapsed_min = max(0, (effective_now(conn) - placed).total_seconds() // 60)
    idx = 0
    for i, at_min in enumerate(FOOD_STAGE_AT_MIN):
        if elapsed_min >= at_min:
            idx = i
    stage = FOOD_STAGES[idx]
    progress = min(100, int(elapsed_min / FOOD_TOTAL_MIN * 100))
    return {
        "id": row["id"],
        "source": row["source"],
        "item_name": row["item_name"],
        "note": row["note"],
        "stage_key": stage["key"],
        "stage_label": stage["label"],
        "stage_index": idx,
        "message": stage["msg"],
        "progress": progress,
        "placed_at": row["placed_at"],
        "delivered": stage["key"] == "delivered",
    }
