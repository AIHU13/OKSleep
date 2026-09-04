"""深夜计划：工作型/服务型 Agent Mock 行为测试。"""
from datetime import datetime, timedelta

import pytest

from app import clock
from app.services import intervention_service, session_service, work_service
from app.services.errors import RuleError


def _working_stage3(conn):
    clock.set_virtual_now(conn, clock.combine_date_hm(datetime(2026, 9, 3).date(), "23:00"))
    sess = session_service.start_session(conn)
    intervention_service.start_flow(conn, sess, "working")
    sess = session_service.active_session(conn)
    intervention_service.act(conn, sess, "continue")  # -> STAGE_2
    sess = session_service.active_session(conn)
    intervention_service.act(conn, sess, "continue")  # -> STAGE_3
    sess = session_service.active_session(conn)
    assert sess.state == "STAGE_3" and sess.scenario == "working"
    return sess


def test_work_task_progress_by_virtual_time(conn):
    sess = _working_stage3(conn)
    task = work_service.start_work_task(conn, "ppt", sess.id)
    assert task["status"] == "queued" and task["progress"] == 0

    # 推进 5 分钟 -> running 50%
    clock.set_virtual_now(conn, clock.effective_now(conn) + timedelta(minutes=5))
    items = work_service.tasks(conn, sess.id)
    assert items[0]["status"] == "running" and items[0]["progress"] == 50

    # 推进满 10 分钟 -> done
    clock.set_virtual_now(conn, clock.effective_now(conn) + timedelta(minutes=5))
    items = work_service.tasks(conn, sess.id)
    assert items[0]["status"] == "done" and items[0]["progress"] == 100
    assert "PPT" in (items[0]["result"] or "")


def test_work_task_rule_scenario_and_stage(conn):
    # 刷短视频场景不可用深夜计划
    clock.set_virtual_now(conn, clock.combine_date_hm(datetime(2026, 9, 3).date(), "23:00"))
    sess = session_service.start_session(conn)
    intervention_service.start_flow(conn, sess, "shorts")
    sess = session_service.active_session(conn)
    intervention_service.act(conn, sess, "continue")
    sess = session_service.active_session(conn)
    intervention_service.act(conn, sess, "continue")
    sess = session_service.active_session(conn)
    with pytest.raises(RuleError):
        work_service.start_work_task(conn, "ppt", sess.id)

    # 清理后验证：加班但未到 Stage 3 也不可用
    from app.db.init_db import reset_demo_state

    reset_demo_state(conn)
    clock.set_virtual_now(conn, clock.combine_date_hm(datetime(2026, 9, 4).date(), "23:00"))
    sess3 = session_service.start_session(conn)
    intervention_service.start_flow(conn, sess3, "working")  # STAGE_1
    with pytest.raises(RuleError):
        work_service.start_work_task(conn, "summary", sess3.id)


def test_food_order_stages(conn):
    order = work_service.place_food_order(conn, "redeem_breakfast", note="送到公司前台")
    assert order["stage_key"] == "placed" and order["delivered"] is False

    # 下单 14 分钟后送达
    clock.set_virtual_now(conn, clock.effective_now(conn) + timedelta(minutes=14))
    items = work_service.food_orders(conn)
    assert items[0]["stage_key"] == "delivered" and items[0]["delivered"] is True

    # 加班深夜计划内预定早餐（服务 Agent 来源）
    sess = _working_stage3(conn)
    order2 = work_service.place_food_order(conn, "work_agent", item_name="元气早餐（燕麦+鸡蛋）")
    assert order2["item_name"] == "元气早餐（燕麦+鸡蛋）"
