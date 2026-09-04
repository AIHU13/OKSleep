"""干预服务：状态推进 + 文案生成落库。

State 推进全部经由 Rule Engine（agent.state.can_transition），
文案统一由 Planner 生成（LLM 优先，失败回退 Mock），并写入 interventions 表。
"""
from __future__ import annotations

import sqlite3
from datetime import timedelta

from ..agent import state as sm
from ..agent.planner import planner
from ..agent.policy import build_context
from ..clock import effective_now, fmt, parse_dt
from ..db.database import query_one
from ..models.intervention import INTERVENTION_TABLE
from ..models.session import SLEEP_SESSION_TABLE
from ..models.user import USER_PROFILE_TABLE, UserProfile
from ..mock.scenarios import SCENARIOS, get_content
from .content_service import pick_by_type
from .errors import RuleError


# --------------------------------------------------------------------------
# 基础读写
# --------------------------------------------------------------------------

def _profile_row(conn: sqlite3.Connection) -> UserProfile:
    row = query_one(conn, f"SELECT * FROM {USER_PROFILE_TABLE} WHERE id = 1")
    if not row:
        raise RuleError("用户不存在", code="user_not_found", http_status=404)
    return UserProfile.from_row(row)


def _load_session(conn: sqlite3.Connection, session_id: int):
    row = query_one(conn, f"SELECT * FROM {SLEEP_SESSION_TABLE} WHERE id = ?", (session_id,))
    if not row:
        raise RuleError("会话不存在", code="session_not_found", http_status=404)
    from ..models.session import SleepSession

    return SleepSession.from_row(row)


def _update_session(conn: sqlite3.Connection, session_id: int, **fields) -> None:
    if not fields:
        return
    fields["updated_at"] = fmt(effective_now(conn))
    sets = ", ".join(f"{k} = ?" for k in fields)
    conn.execute(
        f"UPDATE {SLEEP_SESSION_TABLE} SET {sets} WHERE id = ?",
        (*fields.values(), session_id),
    )
    conn.commit()


def _transition(conn: sqlite3.Connection, session, target: str) -> None:
    """Rule Engine 统一入口：非法转移直接抛错。"""
    if not sm.can_transition(session.state, target):
        raise RuleError(
            f"当前状态 {session.state} 不允许进入 {target}（规则约束）",
            code="invalid_transition",
        )
    _update_session(conn, session.id, state=target)


# --------------------------------------------------------------------------
# 消息生成
# --------------------------------------------------------------------------

def _generate_and_log(
    conn: sqlite3.Connection,
    session,
    profile,
    action: str | None = None,
) -> dict:
    """按当前 session 状态生成干预文案（Planner）并落库，返回 {text, suggestion, source}。"""
    content = None
    if session.content_id:
        content = get_content(session.content_id)

    ctx = build_context(
        profile=profile,
        now=effective_now(conn),
        scenario=session.scenario or "",
        state=session.state,
        stage=session.stage,
        featured_content=content,
        streak_days=profile.streak_days,
    )
    msg = planner.generate(ctx)
    conn.execute(
        f"""INSERT INTO {INTERVENTION_TABLE}
            (session_id, state, stage, action, scenario, source, text, suggestion, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            session.id,
            session.state,
            session.stage,
            action,
            session.scenario,
            msg["source"],
            msg["text"],
            msg.get("suggestion") or None,
            fmt(effective_now(conn)),
        ),
    )
    conn.commit()
    return msg


def latest_message(conn: sqlite3.Connection, session_id: int) -> dict:
    row = query_one(
        conn,
        f"SELECT text, suggestion, source FROM {INTERVENTION_TABLE} "
        f"WHERE session_id = ? ORDER BY id DESC LIMIT 1",
        (session_id,),
    )
    if row:
        return {
            "text": row["text"],
            "suggestion": row["suggestion"],
            "source": row["source"],
        }
    return {"text": "", "suggestion": "", "source": "rule"}


# --------------------------------------------------------------------------
# 状态推进
# --------------------------------------------------------------------------

def start_flow(
    conn: sqlite3.Connection,
    session,
    scenario: str,
    content_type: str | None = None,
) -> None:
    """BEDTIME_START -> STAGE_1；scenario=ready 直接 -> SLEEP_MODE（内容由用户选择）。"""
    if session.state != sm.STATE_BEDTIME_START:
        raise RuleError("会话不在待选择场景状态", code="state_conflict")
    if scenario not in SCENARIOS:
        raise RuleError("未知场景", code="bad_scenario", http_status=422)
    profile = _profile_row(conn)

    if scenario == "ready":
        _enter_sleep_mode(
            conn, session, profile, action="scenario_ready", content_type=content_type
        )
        return

    _transition(conn, session, sm.STATE_STAGE_1)
    _update_session(conn, session.id, scenario=scenario, stage=1)
    session = _load_session(conn, session.id)
    _generate_and_log(conn, session, profile, action="scenario_chosen")


def act(
    conn: sqlite3.Connection,
    session,
    action: str,
    content_type: str | None = None,
) -> None:
    """用户行为：continue（继续使用）/ prepare_sleep（进入休息）。"""
    profile = _profile_row(conn)

    if action == "continue":
        stage = sm.stage_number(session.state)
        if stage is None or stage >= 3:
            raise RuleError(
                "已经到了最后阶段，今晚请选择进入休息吧", code="stage_final"
            )
        target = sm.state_from_stage(stage + 1)
        _transition(conn, session, target)
        _update_session(conn, session.id, stage=stage + 1)
        session = _load_session(conn, session.id)
        _generate_and_log(conn, session, profile, action="continue")
        return

    if action == "prepare_sleep":
        if sm.stage_number(session.state) is None:
            raise RuleError("当前状态无法进入休息", code="invalid_action")
        _enter_sleep_mode(
            conn, session, profile, action="prepare_sleep", content_type=content_type
        )
        return

    raise RuleError(f"未知行为: {action}", code="bad_action", http_status=422)


def _enter_sleep_mode(
    conn: sqlite3.Connection,
    session,
    profile,
    action: str,
    content_type: str | None = None,
) -> None:
    """进入 Sleep Mode。

    内容策略：用户显式选择 -> 播放所选类型首篇；
    未选择 -> 安静休息（不自动播放）。AI 个性化推荐能力见前端说明。
    """
    _transition(conn, session, sm.STATE_SLEEP_MODE)
    content = pick_by_type(content_type, profile.preferred_content)
    now = effective_now(conn)
    _update_session(
        conn,
        session.id,
        content_id=content["id"] if content else None,
        content_type=content["type"] if content else None,
        sleep_started_at=fmt(now),
        scenario=session.scenario,  # 保持原场景
        stage=None,
    )
    session = _load_session(conn, session.id)
    _generate_and_log(conn, session, profile, action=action)


# --------------------------------------------------------------------------
# 成功检测
# --------------------------------------------------------------------------

def check_sleep_success(conn: sqlite3.Connection, session) -> bool:
    """SLEEP_MODE 下模拟 1 小时未使用手机 -> SLEEP_SUCCESS（设计说明 §3.6）。"""
    if session.state != sm.STATE_SLEEP_MODE or not session.sleep_started_at:
        return False
    elapsed = effective_now(conn) - parse_dt(session.sleep_started_at)
    if elapsed >= timedelta(minutes=sm.SLEEP_SUCCESS_MINUTES):
        _transition(conn, session, sm.STATE_SLEEP_SUCCESS)
        return True
    return False


# --------------------------------------------------------------------------
# 视图
# --------------------------------------------------------------------------

def build_session_view(conn: sqlite3.Connection, session_id: int) -> dict:
    session = _load_session(conn, session_id)
    check_sleep_success(conn, session)
    session = _load_session(conn, session_id)
    return _compose_view(conn, session)


def _compose_view(conn: sqlite3.Connection, session) -> dict:
    now = effective_now(conn)
    scenario = SCENARIOS.get(session.scenario or "", {})
    content = get_content(session.content_id) if session.content_id else None

    can_act: list[str] = []
    if session.state in (sm.STATE_STAGE_1, sm.STATE_STAGE_2):
        can_act = ["continue", "prepare_sleep"]
    elif session.state == sm.STATE_STAGE_3:
        can_act = ["prepare_sleep"]

    remaining_sec: int | None = None
    elapsed_min: int | None = None
    if session.state == sm.STATE_SLEEP_MODE and session.sleep_started_at:
        started = parse_dt(session.sleep_started_at)
        elapsed = now - started
        elapsed_min = max(0, int(elapsed.total_seconds() // 60))
        remaining_sec = max(
            0, sm.SLEEP_SUCCESS_MINUTES * 60 - int(elapsed.total_seconds())
        )

    message = latest_message(conn, session.id)
    return {
        "session_id": session.id,
        "date": session.date,
        "state": session.state,
        "stage": session.stage,
        "stage_label": sm.STAGE_LABELS.get(session.state, ""),
        "scenario": session.scenario,
        "scenario_name": scenario.get("name", ""),
        "scenario_icon": scenario.get("icon", ""),
        "content": content,
        "message": message,
        "can_act": can_act,
        "sleep": {
            "started_at": session.sleep_started_at,
            "remaining_sec": remaining_sec,
            "elapsed_min": elapsed_min,
        },
        "updated_at": session.updated_at,
        "reward_ready": session.state == sm.STATE_SLEEP_SUCCESS,
    }
