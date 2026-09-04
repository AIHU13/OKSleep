"""Demo Control 路由：模拟时间与重置（设计说明 §4 隐藏面板）。"""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends

from ..db.database import get_db
from ..schemas.session import AdvanceIn
from ..services import session_service

router = APIRouter(prefix="/api/demo", tags=["demo"])


@router.post("/enter-window")
def enter_window(conn: sqlite3.Connection = Depends(get_db)) -> dict:
    """模拟：进入睡前 30 分钟。"""
    session_service.demo_enter_window(conn)
    return session_service.current_view(conn)


@router.post("/advance")
def advance(body: AdvanceIn, conn: sqlite3.Connection = Depends(get_db)) -> dict:
    """模拟：时间前进 N 分钟（默认 6，用于 Stage 2）。"""
    session_service.demo_advance(conn, body.minutes)
    return session_service.current_view(conn)


@router.post("/next-day")
def next_day(conn: sqlite3.Connection = Depends(get_db)) -> dict:
    """模拟：第二天早上。"""
    session_service.demo_next_day(conn)
    return session_service.current_view(conn)


@router.post("/reset")
def reset(conn: sqlite3.Connection = Depends(get_db)) -> dict:
    """重置 Demo：清空业务数据与虚拟时间。"""
    session_service.reset_demo(conn)
    return session_service.current_view(conn)
