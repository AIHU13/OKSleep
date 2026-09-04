"""Agent 路由：场景选择、行为推进、会话视图、内容目录。"""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends

from ..db.database import get_db
from ..mock.scenarios import SCENARIOS
from ..schemas.agent import ActIn, ScenarioStartIn
from ..services import intervention_service, session_service
from ..services.content_service import TYPE_LABELS, list_grouped
from ..services.errors import RuleError

router = APIRouter(prefix="/api/agent", tags=["agent"])


def _active_or_404(conn: sqlite3.Connection):
    sess = session_service.active_session(conn)
    if not sess:
        raise RuleError("还没有进行中的睡前流程", code="no_active_session", http_status=404)
    return sess


@router.post("/start")
def choose_scenario(
    body: ScenarioStartIn, conn: sqlite3.Connection = Depends(get_db)
) -> dict:
    """选择当前状态后启动分阶段干预（BEDTIME_START -> STAGE_1 / SLEEP_MODE）。"""
    sess = _active_or_404(conn)
    intervention_service.start_flow(conn, sess, body.scenario, body.content_type)
    return session_service.current_view(conn)


@router.post("/act")
def act(body: ActIn, conn: sqlite3.Connection = Depends(get_db)) -> dict:
    """用户行为：continue（继续使用）/ prepare_sleep（进入休息）。"""
    sess = _active_or_404(conn)
    intervention_service.act(conn, sess, body.action, body.content_type)
    return session_service.current_view(conn)


@router.get("/view")
def view(conn: sqlite3.Connection = Depends(get_db)) -> dict:
    """当前会话详情（刷新页面恢复场景用）。"""
    sess = _active_or_404(conn)
    return intervention_service.build_session_view(conn, sess.id)


@router.get("/scenarios")
def scenarios() -> dict:
    """三种模拟场景目录。"""
    return {"items": [SCENARIOS[k] for k in SCENARIOS]}


@router.get("/contents")
def contents() -> dict:
    """助眠内容目录（按类型分组）。"""
    grouped = list_grouped()
    return {
        "type_labels": TYPE_LABELS,
        "groups": [
            {"type": t, "label": TYPE_LABELS.get(t, t), "items": grouped[t]}
            for t in grouped
        ],
    }
