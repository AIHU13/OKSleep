"""时间工具与 Demo 虚拟时钟。

MVP 原则（设计说明 §3.4/3.6、规范第 13 条）：所有真实等待时间都必须提供 Demo 模拟能力。
实现方式：demo_state 表保存 virtual_now；设置后一切业务以虚拟时间为准，
便于"进入睡前30分钟 / 模拟6分钟 / 模拟1小时 / 模拟第二天 / 重置Demo"。
"""
from __future__ import annotations

import sqlite3
from datetime import date, datetime, timedelta
from typing import Optional

TIME_FMT = "%Y-%m-%d %H:%M:%S"
DATE_FMT = "%Y-%m-%d"


# --------------------------------------------------------------------------
# 纯函数（可测试）
# --------------------------------------------------------------------------

def now_dt() -> datetime:
    """当前本地时间，去除微秒。"""
    return datetime.now().replace(microsecond=0)


def parse_hm(value: str) -> tuple[int, int]:
    h, m = value.strip().split(":")
    return int(h), int(m)


def hm_to_minutes(value: str) -> int:
    h, m = parse_hm(value)
    return h * 60 + m


def minutes_to_hm(total: int) -> str:
    total = max(0, int(total))
    return f"{total // 60:02d}:{total % 60:02d}"


def combine_date_hm(day: date, hm: str) -> datetime:
    h, m = parse_hm(hm)
    return datetime(day.year, day.month, day.day, h, m)


def fmt(dt: datetime) -> str:
    return dt.strftime(TIME_FMT)


def parse_dt(text: str) -> datetime:
    return datetime.strptime(text, TIME_FMT)


def fmt_date(d: date) -> str:
    return d.strftime(DATE_FMT)


def parse_date(text: str) -> date:
    return datetime.strptime(text, DATE_FMT).date()


def add_days(d: date, days: int) -> date:
    return d + timedelta(days=days)


# --------------------------------------------------------------------------
# 虚拟时钟（需要 DB 连接）
# --------------------------------------------------------------------------

def _ensure_row(conn: sqlite3.Connection) -> None:
    conn.execute("INSERT OR IGNORE INTO demo_state (id, virtual_now, updated_at) VALUES (1, NULL, NULL)")


def is_demo_time(conn: sqlite3.Connection) -> bool:
    """是否处于 Demo 虚拟时间。"""
    _ensure_row(conn)
    row = conn.execute("SELECT virtual_now FROM demo_state WHERE id = 1").fetchone()
    return bool(row and row["virtual_now"])


def get_virtual_now(conn: sqlite3.Connection) -> Optional[datetime]:
    _ensure_row(conn)
    row = conn.execute("SELECT virtual_now FROM demo_state WHERE id = 1").fetchone()
    text = row["virtual_now"] if row else None
    return parse_dt(text) if text else None


def effective_now(conn: sqlite3.Connection) -> datetime:
    """业务统一使用的时间：Demo 开启时取虚拟时间，否则取真实时间。"""
    virtual = get_virtual_now(conn)
    return virtual if virtual else now_dt()


def set_virtual_now(conn: sqlite3.Connection, dt: datetime) -> None:
    _ensure_row(conn)
    conn.execute(
        "UPDATE demo_state SET virtual_now = ?, updated_at = ? WHERE id = 1",
        (fmt(dt), fmt(now_dt())),
    )
    conn.commit()


def advance_virtual(conn: sqlite3.Connection, minutes: int) -> datetime:
    """虚拟时间前进 minutes 分钟；未开启时按当前真实时间起算。"""
    base = effective_now(conn)
    target = base + timedelta(minutes=int(minutes))
    set_virtual_now(conn, target)
    return target


def clear_virtual_now(conn: sqlite3.Connection) -> None:
    """重置 Demo：恢复真实时间。"""
    _ensure_row(conn)
    conn.execute(
        "UPDATE demo_state SET virtual_now = NULL, updated_at = ? WHERE id = 1",
        (fmt(now_dt()),),
    )
    conn.commit()
