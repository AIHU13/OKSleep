"""深夜计划路由：目录 / 草稿配置 / 启动 / 会话要点 / 次日报告。"""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends

from ..db.database import get_db
from ..schemas.deep_night import ActivateIn, PlanConfigIn
from ..services import deep_night_service

router = APIRouter(prefix="/api/plan", tags=["deep-night"])


@router.get("/types")
def catalog() -> dict:
    return deep_night_service.catalog()


@router.get("/draft")
def draft(conn: sqlite3.Connection = Depends(get_db)) -> dict:
    return deep_night_service.draft(conn)


@router.post("/config")
def config_draft(body: PlanConfigIn, conn: sqlite3.Connection = Depends(get_db)) -> dict:
    tasks = [t.model_dump() for t in body.tasks]
    return deep_night_service.config_draft(conn, tasks)


@router.post("/activate")
def activate(body: ActivateIn, conn: sqlite3.Connection = Depends(get_db)) -> dict:
    return deep_night_service.activate(conn, body.session_id)


@router.get("/session")
def session_plan(session_id: int, conn: sqlite3.Connection = Depends(get_db)) -> dict:
    return deep_night_service.session_plan(conn, session_id)


@router.get("/report")
def report(session_id: int, conn: sqlite3.Connection = Depends(get_db)) -> dict:
    return deep_night_service.report(conn, session_id)
