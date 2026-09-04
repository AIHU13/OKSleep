"""深夜计划：草稿配置 / Stage3 启动 / 次日交付看板 测试。"""
from datetime import datetime

import pytest

from app import clock
from app.services import deep_night_service, intervention_service, session_service
from app.services.errors import RuleError


def _goto_window(conn, day=None):
    day = day or datetime(2026, 9, 3).date()
    clock.set_virtual_now(conn, clock.combine_date_hm(day, "23:00"))


def _working_stage3(conn, day=None):
    _goto_window(conn, day)
    sess = session_service.start_session(conn)
    intervention_service.start_flow(conn, sess, "working")
    sess = session_service.active_session(conn)
    intervention_service.act(conn, sess, "continue")
    sess = session_service.active_session(conn)
    intervention_service.act(conn, sess, "continue")
    return session_service.active_session(conn)


def _sample_tasks():
    return [
        {
            "category": "daily",
            "task_type": "breakfast",
            "title": "预定早餐",
            "params": {"deliver_at": "08:30", "note": "少冰豆浆"},
        },
        {
            "category": "work",
            "task_type": "weekly_report",
            "title": "周报撰写",
            "params": {"workspace": "数据中台 · 周会工作区", "spec_doc": "weekly_v2"},
        },
        {
            "category": "work",
            "task_type": "ppt",
            "title": "PPT 制作",
            "params": {
                "workspace": "增长分析 · 工作区",
                "topic": "Q3 用户增长复盘",
                "spec_doc": "presentation",
            },
        },
    ]


def test_config_and_draft(conn):
    out = deep_night_service.config_draft(conn, _sample_tasks())
    assert out["status"] == "draft" and len(out["tasks"]) == 3
    assert any("08:30" in t["point"] for t in out["tasks"])
    assert any("周报" in t["point"] for t in out["tasks"])
    assert any("PPT" in t["point"] for t in out["tasks"])

    # 覆盖保存（清空）
    empty = deep_night_service.config_draft(conn, [])
    assert empty["tasks"] == []


def test_activate_rules(conn):
    from app.db.init_db import reset_demo_state

    deep_night_service.config_draft(conn, _sample_tasks())

    # 任意进行中的场景/阶段都可以启动深夜计划（例如刷短视频 Stage1）
    _goto_window(conn)
    s = session_service.start_session(conn)
    intervention_service.start_flow(conn, s, "shorts")
    s = session_service.active_session(conn)
    plan = deep_night_service.activate(conn, s.id)
    assert plan["status"] == "active" and plan["session_id"] == s.id

    # 加班未到 Stage 3 同样允许
    reset_demo_state(conn)
    _goto_window(conn)
    s2 = session_service.start_session(conn)
    intervention_service.start_flow(conn, s2, "working")  # STAGE_1
    s2 = session_service.active_session(conn)
    plan2 = deep_night_service.activate(conn, s2.id)
    assert plan2["status"] == "active" and len(plan2["tasks"]) == 3

    # 不存在的会话 -> 404
    with pytest.raises(RuleError):
        deep_night_service.activate(conn, 99999)


def test_activate_with_draft_and_default(conn):
    deep_night_service.config_draft(conn, _sample_tasks())
    sess = _working_stage3(conn)
    plan = deep_night_service.activate(conn, sess.id)
    assert plan["status"] == "active"
    assert plan["session_id"] == sess.id
    assert len(plan["tasks"]) == 3

    sp = deep_night_service.session_plan(conn, sess.id)
    assert sp["has_plan"] and sp["task_count"] == 3

    # 幂等
    plan2 = deep_night_service.activate(conn, sess.id)
    assert plan2["plan_id"] == plan["plan_id"]


def test_activate_defaults_when_no_draft(conn):
    sess = _working_stage3(conn)
    plan = deep_night_service.activate(conn, sess.id)
    assert plan["status"] == "active"
    assert len(plan["tasks"]) == 3  # 默认任务集


def test_next_day_report(conn):
    # 配置早 8:30 配送 -> 次日 07:45 时早餐仍在配送中
    deep_night_service.config_draft(conn, _sample_tasks())
    sess = _working_stage3(conn)
    deep_night_service.activate(conn, sess.id)
    session_service.demo_next_day(conn)  # 次日早晨 07:45

    rep = deep_night_service.report(conn, sess.id)
    assert rep["has_plan"] and len(rep["items"]) == 3
    by_type = {i["task_type"]: i for i in rep["items"]}
    # 早餐仍在配送中（08:30 才送达）
    assert by_type["breakfast"]["status"] == "delivering"
    assert "配送中" in by_type["breakfast"]["label"]
    # 周报 / PPT 已完成且可查看
    assert by_type["weekly_report"]["status"] == "done"
    assert by_type["weekly_report"]["artifact"] and "周报" in by_type["weekly_report"]["artifact"]["title"]
    assert by_type["ppt"]["status"] == "done"
    assert by_type["ppt"]["artifact"]["kind"] == "ppt"
