"""会话服务：用户画像、会话生命周期、Demo 时间控制、聚合视图（AppState）。

前端唯一的引导数据源是 GET /session/current 返回的 AppState：
profile + clock + home + session（若有）。
刷新页面后 Session 由后端恢复（规范验收：刷新后 Session 不丢失）。
"""
from __future__ import annotations

import sqlite3
from datetime import timedelta

from ..agent import state as sm
from ..clock import (
    clear_virtual_now,
    combine_date_hm,
    effective_now,
    fmt,
    get_virtual_now,
    is_demo_time,
    now_dt,
    parse_date,
    set_virtual_now,
)
from ..config import settings
from ..db.database import execute, query_all, query_one
from ..models.reward import REWARD_TABLE
from ..models.session import SLEEP_SESSION_TABLE, SleepSession
from ..models.user import USER_PROFILE_TABLE, UserProfile
from .errors import RuleError
from .intervention_service import _compose_view, check_sleep_success


# --------------------------------------------------------------------------
# 用户画像
# --------------------------------------------------------------------------

def get_profile(conn: sqlite3.Connection) -> UserProfile:
    row = query_one(conn, f"SELECT * FROM {USER_PROFILE_TABLE} WHERE id = ?", (settings.demo_user_id,))
    if not row:
        raise RuleError("用户不存在，请先初始化数据库", code="user_not_found", http_status=404)
    return UserProfile.from_row(row)


def update_profile(conn: sqlite3.Connection, patch: dict) -> UserProfile:
    allowed = {
        "weekday_bedtime",
        "weekday_wake",
        "weekend_bedtime",
        "weekend_wake",
        "preferred_content",
    }
    data = {k: v for k, v in patch.items() if k in allowed and v not in (None, "")}
    if not data:
        raise RuleError("没有可更新的字段", code="bad_patch", http_status=422)
    sets = ", ".join(f"{k} = ?" for k in data)
    conn.execute(
        f"UPDATE {USER_PROFILE_TABLE} SET {sets} WHERE id = ?",
        (*data.values(), settings.demo_user_id),
    )
    conn.commit()
    return get_profile(conn)


# --------------------------------------------------------------------------
# 会话生命周期
# --------------------------------------------------------------------------

def active_session(conn: sqlite3.Connection) -> SleepSession | None:
    """最近一个未终结的会话（刷新页面 / 重复进入时复用）。"""
    row = query_one(
        conn,
        f"SELECT * FROM {SLEEP_SESSION_TABLE} "
        f"WHERE user_id = ? AND state NOT IN ({', '.join('?' for _ in sm.TERMINAL_STATES)}) "
        f"ORDER BY id DESC LIMIT 1",
        (settings.demo_user_id, *sorted(sm.TERMINAL_STATES)),
    )
    return SleepSession.from_row(row) if row else None


def latest_session(conn: sqlite3.Connection) -> SleepSession | None:
    row = query_one(
        conn,
        f"SELECT * FROM {SLEEP_SESSION_TABLE} WHERE user_id = ? ORDER BY id DESC LIMIT 1",
        (settings.demo_user_id,),
    )
    return SleepSession.from_row(row) if row else None


def start_session(conn: sqlite3.Connection) -> SleepSession:
    """开始今晚助眠：IDLE -> BEDTIME_START；已有活跃会话则直接复用（幂等）。"""
    existing = active_session(conn)
    if existing:
        return existing
    now = effective_now(conn)
    sid = execute(
        conn,
        f"""INSERT INTO {SLEEP_SESSION_TABLE}
            (user_id, date, state, started_at, updated_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?)""",
        (
            settings.demo_user_id,
            fmt(now)[:10],
            sm.STATE_BEDTIME_START,
            fmt(now),
            fmt(now),
            fmt(now),
        ),
    )
    return SleepSession(
        id=sid,
        user_id=settings.demo_user_id,
        date=fmt(now)[:10],
        state=sm.STATE_BEDTIME_START,
        started_at=fmt(now),
        updated_at=fmt(now),
        created_at=fmt(now),
    )


def reset_demo(conn: sqlite3.Connection) -> None:
    """重置 Demo：清空业务表与虚拟时间，回到初始画像。"""
    from ..db.init_db import reset_demo_state

    reset_demo_state(conn)


# --------------------------------------------------------------------------
# Demo 时间控制（规范第 13 条：真实等待必须提供模拟能力）
# --------------------------------------------------------------------------

def demo_enter_window(conn: sqlite3.Connection) -> dict:
    """模拟"进入睡前30分钟"：把虚拟时间拨到今晚 T-30。"""
    now = effective_now(conn)
    day = now.date()
    window = sm.window_start(get_profile(conn), day)
    set_virtual_now(conn, window)
    return {"ok": True, "virtual_now": fmt(window)}


def demo_advance(conn: sqlite3.Connection, minutes: int) -> dict:
    from ..clock import advance_virtual

    target = advance_virtual(conn, minutes)
    return {"ok": True, "virtual_now": fmt(target)}


def demo_next_day(conn: sqlite3.Connection) -> dict:
    """模拟"第二天"：虚拟时间跳到下一个早晨（若已过午夜则跳今晨）。

    语义：用户在入睡日晚间进入窗口，模拟 1 小时后入睡成功（通常已跨午夜），
    此时"第二天"指入睡日的次日早晨，而非当前虚拟日 +1 再 +1。
    """
    profile = get_profile(conn)
    now = effective_now(conn)
    day = now.date()
    wake_hm_str = profile.weekend_wake if sm.is_weekend(day) else profile.weekday_wake
    this_morning = combine_date_hm(day, wake_hm_str)
    if now < this_morning:
        target_day = day  # 例如 00:30 -> 今晨 07:30
    else:
        tomorrow = day + timedelta(days=1)
        wake_hm_str = profile.weekend_wake if sm.is_weekend(tomorrow) else profile.weekday_wake
        target_day = tomorrow
    target = combine_date_hm(target_day, wake_hm_str) + timedelta(minutes=15)
    set_virtual_now(conn, target)
    return {"ok": True, "virtual_now": fmt(target)}


# --------------------------------------------------------------------------
# 聚合视图（AppState）
# --------------------------------------------------------------------------

def current_view(conn: sqlite3.Connection) -> dict:
    profile = get_profile(conn)
    now = effective_now(conn)
    phase = sm.phase_of(profile, now)
    sess = active_session(conn)

    session_view = None
    if sess:
        check_sleep_success(conn, sess)  # 读取时惰性判定成功
        # 判定可能推进了状态，必须重载后再组装视图
        row = query_one(
            conn, f"SELECT * FROM {SLEEP_SESSION_TABLE} WHERE id = ?", (sess.id,)
        )
        if row:
            sess = SleepSession.from_row(row)
        session_view = _compose_view(conn, sess)

    profile_out = _profile_out(profile)
    profile_out["completed_nights"] = count_completed(conn)
    virtual = get_virtual_now(conn)
    return {
        "profile": profile_out,
        "meta": {"needs_setup": needs_setup(conn)},
        "clock": {
            "demo_active": is_demo_time(conn),
            "virtual_now": fmt(virtual) if virtual else None,
            "real_now": fmt(now_dt()),
        },
        "home": {
            "phase": phase["phase"],
            "phase_text": phase["phase_text"],
            "bedtime_hm": sm.bedtime_hm(profile, now.date()),
            "wake_hm": sm.wake_hm(profile, now.date()),
            "window_start": fmt(phase["window_start"]),
            "bedtime": fmt(phase["bedtime"]),
            "wake": fmt(phase["wake"]),
            "is_in_window": phase["phase"] == "in_window",
            "can_start": sess is None,
        },
        "session": session_view,
    }


def profile_view(conn: sqlite3.Connection) -> dict:
    out = _profile_out(get_profile(conn))
    out["completed_nights"] = count_completed(conn)
    return out


def count_completed(conn: sqlite3.Connection) -> int:
    """已完成的成功夜晚数（结算过奖励的入睡夜，每晚去重计 1）。"""
    row = query_one(
        conn,
        f"SELECT COUNT(*) AS c FROM {REWARD_TABLE} r "
        f"JOIN {SLEEP_SESSION_TABLE} s ON s.id = r.session_id "
        f"WHERE r.user_id = ?",
        (settings.demo_user_id,),
    )
    return int(row["c"]) if row else 0


def needs_setup(conn: sqlite3.Connection) -> bool:
    """是否仍需首次配置向导（入睡时间 / 深夜计划等）。"""
    row = query_one(
        conn, "SELECT value FROM meta_flags WHERE key = 'onboarding_done'"
    )
    return row is None or (row["value"] or "0") != "1"


def mark_setup_done(conn: sqlite3.Connection) -> None:
    conn.execute(
        "INSERT INTO meta_flags (key, value) VALUES ('onboarding_done', '1') "
        "ON CONFLICT(key) DO UPDATE SET value = '1'"
    )
    conn.commit()


def _profile_out(profile: UserProfile) -> dict:
    return {
        "weekday_bedtime": profile.weekday_bedtime,
        "weekday_wake": profile.weekday_wake,
        "weekend_bedtime": profile.weekend_bedtime,
        "weekend_wake": profile.weekend_wake,
        "preferred_content": profile.preferred_content,
        "streak_days": profile.streak_days,
        "total_coins": profile.total_coins,
        "last_success_date": profile.last_success_date,
    }


# --------------------------------------------------------------------------
# 历史（验收：历史数据能够保存）
# --------------------------------------------------------------------------

def history(conn: sqlite3.Connection, limit: int = 30) -> list[dict]:
    rows = query_all(
        conn,
        f"""SELECT s.id, s.date, s.state, s.scenario, s.stage,
                   r.coins, r.streak_after AS streak, r.total_after AS total_coins,
                   r.message AS reward_message
            FROM {SLEEP_SESSION_TABLE} s
            LEFT JOIN {REWARD_TABLE} r ON r.session_id = s.id
            WHERE s.user_id = ?
            ORDER BY s.id DESC LIMIT ?""",
        (settings.demo_user_id, int(limit)),
    )
    from ..mock.scenarios import SCENARIOS

    out: list[dict] = []
    for row in rows:
        scenario = SCENARIOS.get(row["scenario"] or "", {})
        state = row["state"]
        result = "进行中"
        if state == sm.STATE_REWARD:
            result = "已完成 · 已领奖"
        elif state in (sm.STATE_SLEEP_SUCCESS, sm.STATE_SLEEP_MODE):
            result = "已完成睡眠 · 待领奖" if state == sm.STATE_SLEEP_SUCCESS else "进入睡眠中"
        out.append(
            {
                "kind": "sleep",
                "session_id": row["id"],
                "date": row["date"],
                "state": state,
                "result": result,
                "scenario": row["scenario"],
                "scenario_name": scenario.get("name", ""),
                "scenario_icon": scenario.get("icon", ""),
                "stage": row["stage"],
                "coins": row["coins"],
                "streak": row["streak"],
                "total_coins": row["total_coins"],
                "reward_message": row["reward_message"],
            }
        )

    # 助眠失败记录（手机场景模拟：深夜未按时休息）
    from ..models.miss import MISS_TABLE

    miss_rows = query_all(
        conn,
        f"SELECT * FROM {MISS_TABLE} WHERE user_id = ? ORDER BY id DESC LIMIT ?",
        (settings.demo_user_id, int(limit)),
    )
    for m in miss_rows:
        out.append(
            {
                "kind": "miss",
                "session_id": None,
                "date": m["date"],
                "state": "MISSED",
                "result": "助眠失败 · 未按时进入睡眠",
                "scenario": m["scenario"],
                "scenario_name": "深夜仍在刷手机",
                "scenario_icon": "🚫",
                "stage": None,
                "coins": -m["coins_deducted"],
                "streak": None,
                "total_coins": None,
                "reward_message": m["message"],
            }
        )

    # 同日内：失败记录展示在前（更贴近时间顺序），整体按日期倒序
    out.sort(key=lambda x: (x["date"], 0 if x["kind"] == "sleep" else 1), reverse=True)
    return out[: int(limit)]
