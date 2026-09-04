"""奖励路由：次日结算 / 最新奖励 / 助眠失败记录 / 历史。"""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends

from ..db.database import get_db
from ..schemas.reward import MissIn, SettleIn
from ..services import reward_service, session_service

router = APIRouter(prefix="/api/reward", tags=["reward"])


@router.post("/settle")
def settle(body: SettleIn, conn: sqlite3.Connection = Depends(get_db)) -> dict:
    return reward_service.settle(conn, body.session_id)


@router.post("/miss")
def record_miss(body: MissIn, conn: sqlite3.Connection = Depends(get_db)) -> dict:
    return reward_service.miss(conn, body.scenario)


@router.get("/latest")
def latest(conn: sqlite3.Connection = Depends(get_db)) -> dict | None:
    return reward_service.latest(conn)


@router.get("/history")
def history(conn: sqlite3.Connection = Depends(get_db)) -> dict:
    return {"items": session_service.history(conn)}
