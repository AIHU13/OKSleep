"""会话路由：当前视图（AppState 单源）/ 开始助眠。"""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends

from ..db.database import get_db
from ..services import session_service

router = APIRouter(prefix="/api/session", tags=["session"])


@router.get("/current")
def current(conn: sqlite3.Connection = Depends(get_db)) -> dict:
    """AppState：profile + clock + home + session（前端唯一引导数据源）。"""
    return session_service.current_view(conn)


@router.post("/start")
def start(conn: sqlite3.Connection = Depends(get_db)) -> dict:
    """开始今晚助眠（幂等：已有活跃会话则复用）。"""
    session_service.start_session(conn)
    return session_service.current_view(conn)
