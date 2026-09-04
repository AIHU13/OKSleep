"""深夜计划服务：首页草稿配置 / Stage3 启动 / 次日交付看板。

执行模型（Mock）：任务进度与外卖状态由 Demo 虚拟时间推导，
次日（入睡日 + 1 的早晨）可查看"任务完成情况与交付物"。
接入真实 LLM/Agent 后，替换为真实的任务规划、自主执行与交付。
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta

from ..agent import state as sm
from ..clock import effective_now, fmt, hm_to_minutes, now_dt, parse_date, parse_dt
from ..config import settings
from ..db.database import execute, query_all, query_one
from ..mock.deep_night import (
    CATEGORIES,
    DEFAULT_ACTIVATION_TASKS,
    SPEC_DOCS,
    TASK_TYPE_BY_KEY,
    TASK_TYPES,
    WORK_DURATION_MIN,
    breakfast_artifact,
    ppt_artifact,
    remind_artifact,
    weekly_report_artifact,
)
from ..models.deep_night import (
    DEEP_NIGHT_PLANS_TABLE,
    PLAN_TASKS_TABLE,
    DeepNightPlan,
)
from .errors import RuleError

CATEGORY_BY_KEY = {c["key"]: c["name"] for c in CATEGORIES}


# --------------------------------------------------------------------------
# 目录
# --------------------------------------------------------------------------

def catalog() -> dict:
    return {
        "categories": CATEGORIES,
        "task_types": TASK_TYPES,
        "spec_docs": SPEC_DOCS,
        "default_tasks": DEFAULT_ACTIVATION_TASKS,
    }


# --------------------------------------------------------------------------
# 草稿配置（首页表格）
# --------------------------------------------------------------------------

def draft(conn: sqlite3.Connection) -> dict:
    plan = _latest(conn, "draft")
    if not plan:
        return {"plan_id": None, "status": "draft", "tasks": []}
    return _plan_out(conn, plan, with_artifact=False)


def config_draft(conn: sqlite3.Connection, tasks: list[dict]) -> dict:
    """保存首页配置的任务草稿（全量覆盖），tasks 允许为空。"""
    for t in tasks:
        spec = TASK_TYPE_BY_KEY.get(t.get("task_type"))
        if not spec or spec["category"] != t.get("category"):
            raise RuleError(
                f"未知任务或分类不匹配: {t.get('category')}/{t.get('task_type')}",
                code="bad_task_type",
                http_status=422,
            )

    # 覆盖旧的 draft（含任务）
    old = _latest(conn, "draft")
    if old:
        conn.execute(f"DELETE FROM {PLAN_TASKS_TABLE} WHERE plan_id = ?", (old.id,))
        conn.execute(
            f"DELETE FROM {DEEP_NIGHT_PLANS_TABLE} WHERE id = ?", (old.id,)
        )
        conn.commit()

    if not tasks:
        return {"plan_id": None, "status": "draft", "tasks": []}

    now = now_dt()
    pid = execute(
        conn,
        f"""INSERT INTO {DEEP_NIGHT_PLANS_TABLE}
            (user_id, status, created_at, updated_at) VALUES (?, 'draft', ?, ?)""",
        (settings.demo_user_id, fmt(now), fmt(now)),
    )
    _insert_tasks(conn, pid, tasks, fmt(now))
    plan = query_one(
        conn, f"SELECT * FROM {DEEP_NIGHT_PLANS_TABLE} WHERE id = ?", (pid,)
    )
    from ..models.deep_night import DeepNightPlan

    return _plan_out(conn, DeepNightPlan.from_row(plan), with_artifact=False)


def _insert_tasks(conn: sqlite3.Connection, plan_id: int, tasks: list[dict], created: str) -> None:
    for t in tasks:
        spec = TASK_TYPE_BY_KEY[t["task_type"]]
        title = t.get("title") or spec["name"]
        params = t.get("params") or {}
        params = _normalize_params(spec, params)
        execute(
            conn,
            f"""INSERT INTO {PLAN_TASKS_TABLE}
                (plan_id, user_id, category, task_type, title, params, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                plan_id,
                settings.demo_user_id,
                spec["category"],
                spec["key"],
                title,
                json.dumps(params, ensure_ascii=False),
                created,
            ),
        )


def _normalize_params(spec: dict, params: dict) -> dict:
    out: dict = {}
    for meta in spec["params"]:
        key = meta["key"]
        if meta["type"] == "spec":
            doc = params.get(key) or meta.get("default")
            if doc not in SPEC_DOC_BY_KEYS:
                doc = meta.get("default")
            out[key] = doc
        else:
            out[key] = (params.get(key) if params.get(key) not in (None, "") else meta.get("default")) or ""
    return out


SPEC_DOC_BY_KEYS = {d["key"] for d in SPEC_DOCS}


# --------------------------------------------------------------------------
# 启动（加班 Stage 3 确认）
# --------------------------------------------------------------------------

def activate(conn: sqlite3.Connection, session_id: int) -> dict:
    """启动深夜计划：把当前草稿（或默认任务集）绑定到进行中的助眠会话。

    交互约定：用户在任意干预阶段点「好了，去休息」并选择「是」时调用；
    若首页未配置草稿则使用默认任务集，保证演示可直接运行。
    """
    row = query_one(
        conn,
        f"SELECT id, date FROM {sm_tbl()} WHERE id = ? AND user_id = ?",
        (session_id, settings.demo_user_id),
    )
    if not row:
        raise RuleError("会话不存在", code="session_not_found", http_status=404)

    # 幂等：同一会话已激活则直接返回
    active = query_one(
        conn,
        f"SELECT * FROM {DEEP_NIGHT_PLANS_TABLE} "
        f"WHERE user_id = ? AND session_id = ? AND status = 'active' LIMIT 1",
        (settings.demo_user_id, session_id),
    )
    if active:
        from ..models.deep_night import DeepNightPlan

        return _plan_out(conn, DeepNightPlan.from_row(active), with_artifact=False)

    plan = _latest(conn, "draft")
    now = effective_now(conn)
    if plan:
        # 草稿 -> 激活
        tasks = _tasks_of(conn, plan.id)
        conn.execute(
            f"UPDATE {DEEP_NIGHT_PLANS_TABLE} SET session_id = ?, date = ?, status = 'active', "
            f"updated_at = ? WHERE id = ?",
            (session_id, row["date"], fmt(now), plan.id),
        )
        # 任务计时以激活时刻为准
        conn.execute(
            f"UPDATE {PLAN_TASKS_TABLE} SET created_at = ? WHERE plan_id = ?",
            (fmt(now), plan.id),
        )
        conn.commit()
        from ..models.deep_night import DeepNightPlan

        plan = DeepNightPlan.from_row(
            query_one(
                conn, f"SELECT * FROM {DEEP_NIGHT_PLANS_TABLE} WHERE id = ?", (plan.id,)
            )
        )
        return _plan_out(conn, plan, with_artifact=False)
    else:
        # 无草稿：使用默认任务集
        pid = execute(
            conn,
            f"""INSERT INTO {DEEP_NIGHT_PLANS_TABLE}
                (user_id, session_id, date, status, created_at, updated_at)
                VALUES (?, ?, ?, 'active', ?, ?)""",
            (
                settings.demo_user_id,
                session_id,
                row["date"],
                fmt(now),
                fmt(now),
            ),
        )
        _insert_tasks(conn, pid, DEFAULT_ACTIVATION_TASKS, fmt(now))
        from ..models.deep_night import DeepNightPlan

        plan = DeepNightPlan.from_row(
            query_one(
                conn, f"SELECT * FROM {DEEP_NIGHT_PLANS_TABLE} WHERE id = ?", (pid,)
            )
        )
        return _plan_out(conn, plan, with_artifact=False)


def sm_tbl() -> str:
    from ..models.session import SLEEP_SESSION_TABLE

    return SLEEP_SESSION_TABLE


def session_plan(conn: sqlite3.Connection, session_id: int) -> dict:
    """会话关联的活跃计划（Stage3 展示要点 / Sleep Mode 运行提示）。"""
    row = query_one(
        conn,
        f"SELECT * FROM {DEEP_NIGHT_PLANS_TABLE} "
        f"WHERE user_id = ? AND session_id = ? AND status = 'active' LIMIT 1",
        (settings.demo_user_id, session_id),
    )
    if not row:
        return {"has_plan": False, "points": [], "task_count": 0}
    from ..models.deep_night import DeepNightPlan

    out = _plan_out(conn, DeepNightPlan.from_row(row), with_artifact=False)
    out["has_plan"] = True
    out["task_count"] = len(out.get("tasks") or [])
    return out


# --------------------------------------------------------------------------
# 次日交付看板
# --------------------------------------------------------------------------

def report(conn: sqlite3.Connection, session_id: int) -> dict:
    """次日早晨：展示计划任务完成情况（早餐配送中 / 周报已生成 / PPT 已完成…）。"""
    row = query_one(
        conn,
        f"SELECT * FROM {DEEP_NIGHT_PLANS_TABLE} "
        f"WHERE user_id = ? AND session_id = ? LIMIT 1",
        (settings.demo_user_id, session_id),
    )
    if not row:
        return {"has_plan": False, "items": []}
    from ..models.deep_night import DeepNightPlan

    plan = DeepNightPlan.from_row(row)
    tasks = _tasks_of(conn, plan.id)
    items = [_derive_task(conn, plan, t) for t in tasks]
    # 分类顺序展示
    items.sort(key=lambda x: 0 if x["category"] == "daily" else 1)
    return {
        "has_plan": True,
        "plan_date": plan.date,
        "plan_id": plan.id,
        "items": items,
    }


def _derive_task(conn: sqlite3.Connection, plan, task) -> dict:
    from ..clock import minutes_to_hm

    now = effective_now(conn)
    created = parse_dt(task.created_at)
    elapsed_min = max(0, int((now - created).total_seconds() // 60))
    icon = TASK_TYPE_BY_KEY.get(task.task_type, {}).get("icon", "📌")
    name = CATEGORY_BY_KEY.get(task.category, task.category)
    p = task.params
    deliver_at = p.get("deliver_at") or "07:40"

    def out(status, label, progress=0, artifact=None):
        return {
            "task_id": task.id,
            "category": task.category,
            "category_name": name,
            "task_type": task.task_type,
            "title": task.title,
            "icon": icon,
            "status": status,
            "label": label,
            "progress": progress,
            "artifact": artifact,
        }

    if task.category == "work":
        dur = WORK_DURATION_MIN.get(task.task_type, 20)
        progress = min(100, int(elapsed_min / dur * 100))
        if progress >= 100:
            artifact = _work_artifact(task)
            return out(
                "done",
                f"已完成 · {artifact['title']}（点击查看）",
                100,
                artifact,
            )
        if progress > 0:
            return out("running", f"Agent 执行中 {progress}%（可用 ⚙️ 快进时间）", progress)
        return out("queued", "已加入队列，深夜 Agent 即将开始…", 0)

    # daily
    if plan.date:
        night = parse_date(plan.date)
        morning = night + timedelta(days=1)
    else:
        morning = now.date()
    if task.task_type == "breakfast":
        if now.date() > morning or (now.date() == morning and now.time() >= _hm_time(deliver_at)):
            return out("done", f"早餐已送达（{deliver_at}）", 100, breakfast_artifact(deliver_at, p.get("note", "")))
        if now.date() == morning:
            return out(
                "delivering",
                f"早餐正在配送中 · 预计 {deliver_at} 送达",
                60,
                breakfast_artifact(deliver_at, p.get("note", "")),
            )
        return out("queued", f"已下单 · 明早 {deliver_at} 自动配送", 0, breakfast_artifact(deliver_at, p.get("note", "")))
    # remind
    if now.date() > morning or (now.date() == morning and now.time() >= _hm_time("08:00")):
        return out("done", "明早提醒已送达 ⏰", 100, remind_artifact(p.get("note", "")))
    return out("queued", f"将在明早提醒：{p.get('note') or '重要事项'}", 0)


def _hm_time(hhmm: str) -> datetime.time:
    m = hm_to_minutes(hhmm)
    return (datetime(2000, 1, 1) + timedelta(minutes=m)).time()


def _work_artifact(task) -> dict:
    p = task.params
    if task.task_type == "ppt":
        return ppt_artifact(p.get("topic") or task.title)
    if task.task_type == "weekly_report":
        return weekly_report_artifact()
    return {"kind": "doc", "title": task.title, "body": f"{task.title} 已生成 ✅"}


# --------------------------------------------------------------------------
# 内部工具
# --------------------------------------------------------------------------

def _latest(conn: sqlite3.Connection, status: str) -> DeepNightPlan | None:
    row = query_one(
        conn,
        f"SELECT * FROM {DEEP_NIGHT_PLANS_TABLE} "
        f"WHERE user_id = ? AND status = ? ORDER BY id DESC LIMIT 1",
        (settings.demo_user_id, status),
    )
    return DeepNightPlan.from_row(row) if row else None


def _tasks_of(conn: sqlite3.Connection, plan_id: int):
    from ..models.deep_night import PlanTask

    rows = query_all(
        conn,
        f"SELECT * FROM {PLAN_TASKS_TABLE} WHERE plan_id = ? ORDER BY id ASC",
        (plan_id,),
    )
    return [PlanTask.from_row(r) for r in rows]


def _point_text(task) -> str:
    icon = TASK_TYPE_BY_KEY.get(task.task_type, {}).get("icon", "·")
    p = task.params
    if task.task_type == "breakfast":
        return f"{icon} 早餐：明早 {p.get('deliver_at', '07:40')} 自动配送"
    if task.task_type == "remind":
        return f"{icon} 提醒：明早提醒「{p.get('note') or '重要事项'}」"
    doc = p.get("spec_doc") or ""
    doc_name = ""
    for d in SPEC_DOCS:
        if d["key"] == doc:
            doc_name = d["name"]
            break
    ws = p.get("workspace") or "默认工作区"
    if task.task_type == "ppt":
        return f"{icon} PPT：《{p.get('topic') or task.title}》 按 {doc_name} 在工作区「{ws}」生成"
    return f"{icon} 周报：按 {doc_name} 在工作区「{ws}」自动撰写"


def _plan_out(conn: sqlite3.Connection, plan, with_artifact: bool = False) -> dict:
    tasks = _tasks_of(conn, plan.id)
    items = []
    for t in tasks:
        item = {
            "task_id": t.id,
            "category": t.category,
            "category_name": CATEGORY_BY_KEY.get(t.category, ""),
            "task_type": t.task_type,
            "title": t.title,
            "icon": TASK_TYPE_BY_KEY.get(t.task_type, {}).get("icon", "📌"),
            "point": _point_text(t),
            "params": t.params,
        }
        items.append(item)
    return {
        "plan_id": plan.id,
        "session_id": plan.session_id,
        "date": plan.date,
        "status": plan.status,
        "tasks": items,
    }
