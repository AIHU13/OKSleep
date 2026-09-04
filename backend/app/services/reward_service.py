"""奖励服务：次日奖励结算（+10 Sleep Coins / 连续打卡 +1）。

规则（设计说明 §3.7）：
- 仅在 SLEEP_SUCCESS 且"第二天"（结算日 > 入睡日）可结算；
- 与上次成功入睡日连续则 streak+1，否则重置为 1；
- 幂等：同一 session 重复结算返回已有记录。
"""
from __future__ import annotations

import sqlite3
from datetime import timedelta

from ..agent import state as sm
from ..clock import effective_now, fmt, now_dt, parse_date
from ..config import settings
from ..db.database import execute, query_one
from ..models.reward import REWARD_TABLE
from ..models.session import SLEEP_SESSION_TABLE
from ..models.user import USER_PROFILE_TABLE
from .errors import RuleError

COINS = sm.COINS_PER_SUCCESS


def settle(conn: sqlite3.Connection, session_id: int | None = None) -> dict:
    from .session_service import active_session, get_profile

    profile = get_profile(conn)
    session = None
    if session_id:
        row = query_one(
            conn, f"SELECT * FROM {SLEEP_SESSION_TABLE} WHERE id = ?", (session_id,)
        )
        if not row:
            raise RuleError("会话不存在", code="session_not_found", http_status=404)
        from ..models.session import SleepSession

        session = SleepSession.from_row(row)
    else:
        session = active_session(conn)
        if not session:
            raise RuleError("没有可结算的会话", code="no_session")

    # 幂等1：同一会话已结算 -> 直接返回
    existing = query_one(
        conn, f"SELECT * FROM {REWARD_TABLE} WHERE session_id = ?", (session.id,)
    )
    if existing:
        return _record_out(existing, already=True)

    # 幂等2：同一"夜晚"（入睡日）已结算过（多轮/重复演示同一天）-> 不重复计分
    dup_night = query_one(
        conn,
        f"""SELECT r.* FROM {REWARD_TABLE} r
            JOIN {SLEEP_SESSION_TABLE} s ON s.id = r.session_id
            WHERE r.user_id = ? AND s.date = ? LIMIT 1""",
        (session.user_id, session.date),
    )
    if dup_night:
        return _record_out(dup_night, already=True)

    if session.state != sm.STATE_SLEEP_SUCCESS:
        raise RuleError(
            "尚未确认睡眠成功，还不能结算奖励", code="not_success"
        )

    settle_at = effective_now(conn)
    night_date = parse_date(session.date)
    # “第二天”= 入睡日的次日早晨起床之后（例如 23:30 入睡 -> 次日 07:30+）
    wake_dt = sm.wake_datetime(profile, night_date)
    if settle_at < wake_dt:
        raise RuleError(
            "还没到第二天早晨，请先点击「模拟第二天」再来领取奖励",
            code="need_next_day",
        )

    # 连续打卡：与上一次成功入睡日相邻则 +1，否则重新从 1 开始
    last = parse_date(profile.last_success_date) if profile.last_success_date else None
    if last and night_date == last + timedelta(days=1):
        streak = profile.streak_days + 1
    else:
        streak = 1

    total = profile.total_coins + COINS
    message = "昨晚完成了睡前计划，奖励已到账 🎉"
    rid = execute(
        conn,
        f"""INSERT INTO {REWARD_TABLE}
            (session_id, user_id, date, coins, streak_after, total_after, message, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            session.id,
            session.user_id,
            fmt(settle_at)[:10],
            COINS,
            streak,
            total,
            message,
            fmt(now_dt()),
        ),
    )
    conn.execute(
        f"UPDATE {USER_PROFILE_TABLE} "
        f"SET streak_days = ?, total_coins = ?, last_success_date = ? WHERE id = ?",
        (streak, total, session.date, settings.demo_user_id),
    )
    conn.execute(
        f"UPDATE {SLEEP_SESSION_TABLE} SET state = ?, updated_at = ? WHERE id = ?",
        (sm.STATE_REWARD, fmt(now_dt()), session.id),
    )
    conn.commit()

    row = query_one(conn, f"SELECT * FROM {REWARD_TABLE} WHERE id = ?", (rid,))
    return _record_out(row, already=False)


def miss(conn: sqlite3.Connection, scenario: str | None = None) -> dict:
    """记录一次助眠失败并扣除积分（手机场景模拟：深夜未按时休息）。

    规则：扣除 5 Sleep Coins（积分不足则扣至 0）；记录进入睡眠历史。
    """
    from ..models.miss import MISS_TABLE
    from .session_service import get_profile

    profile = get_profile(conn)
    deduct = min(5, profile.total_coins)
    total_after = profile.total_coins - deduct
    now = effective_now(conn)
    conn.execute(
        f"UPDATE {USER_PROFILE_TABLE} SET total_coins = ? WHERE id = ?",
        (total_after, settings.demo_user_id),
    )
    conn.execute(
        f"""INSERT INTO {MISS_TABLE}
            (user_id, date, scenario, coins_deducted, message, created_at)
            VALUES (?, ?, ?, ?, ?, ?)""",
        (
            settings.demo_user_id,
            fmt(now)[:10],
            scenario or "shorts",
            deduct,
            "助眠失败：深夜仍未按时进入睡眠，已扣除积分提醒",
            fmt(now_dt()),
        ),
    )
    conn.commit()
    return {
        "coins_deducted": deduct,
        "coins_left": total_after,
        "message": (
            f"已记录一次助眠失败，扣除 {deduct} Sleep Coins（剩余 {total_after}）"
            if deduct > 0
            else "已记录一次助眠失败（当前积分不足，未额外扣减）"
        ),
    }


def latest(conn: sqlite3.Connection) -> dict | None:
    row = query_one(
        conn,
        f"SELECT * FROM {REWARD_TABLE} WHERE user_id = ? ORDER BY id DESC LIMIT 1",
        (settings.demo_user_id,),
    )
    return _record_out(row) if row else None


def _record_out(row, already: bool = False) -> dict:
    return {
        "already": already,
        "id": row["id"],
        "session_id": row["session_id"],
        "date": row["date"],
        "coins": row["coins"],
        "streak_days": row["streak_after"],
        "total_coins": row["total_after"],
        "message": row["message"],
    }
