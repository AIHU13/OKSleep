"""完整演示链路测试：开始 → 场景 → 三阶段 → Sleep Mode → 模拟1小时 → 次日奖励。"""
from datetime import datetime, timedelta

import pytest

from app import clock
from app.agent import state as sm
from app.db.init_db import reset_demo_state
from app.services import intervention_service, reward_service, session_service
from app.services.errors import RuleError


def _goto_window(conn, day=None):
    """把虚拟时间拨到某日 23:00（工作日 T-30 窗口）。"""
    profile = session_service.get_profile(conn)
    day = day or datetime(2026, 9, 3).date()  # 周四
    target = clock.combine_date_hm(day, "23:00")
    clock.set_virtual_now(conn, target)
    return profile


def _elapsed(conn, base: datetime, minutes: int) -> None:
    clock.set_virtual_now(conn, base + timedelta(minutes=minutes))


def test_full_demo_chain(conn):
    profile = _goto_window(conn)
    assert session_service.get_profile(conn).id == profile.id

    # 1) 开始助眠
    sess = session_service.start_session(conn)
    assert sess.state == sm.STATE_BEDTIME_START

    # 2) 选择场景：刷短视频 -> STAGE_1
    intervention_service.start_flow(conn, sess, "shorts")
    sess = session_service.active_session(conn)
    assert sess.state == sm.STATE_STAGE_1 and sess.stage == 1
    msg = intervention_service.latest_message(conn, sess.id)
    assert msg["text"] and msg["source"] in ("mock", "llm")

    # 3) 三阶段推进
    intervention_service.act(conn, sess, "continue")
    sess = session_service.active_session(conn)
    assert sess.state == sm.STATE_STAGE_2 and sess.stage == 2

    intervention_service.act(conn, sess, "continue")
    sess = session_service.active_session(conn)
    assert sess.state == sm.STATE_STAGE_3 and sess.stage == 3

    # Stage 3 不允许继续刷
    with pytest.raises(RuleError):
        intervention_service.act(conn, sess, "continue")

    # 4) 进入 Sleep Mode（用户选择助眠音乐；不选择则不自动播放）
    intervention_service.act(conn, sess, "prepare_sleep", content_type="music")
    sess = session_service.active_session(conn)
    assert sess.state == sm.STATE_SLEEP_MODE
    assert sess.content_id is not None and sess.sleep_started_at is not None

    # 5) 59 分钟未成功，60 分钟成功
    base = clock.effective_now(conn)
    _elapsed(conn, base, 59)
    assert not intervention_service.check_sleep_success(conn, sess)
    _elapsed(conn, base, 60)
    sess = session_service.active_session(conn)
    assert intervention_service.check_sleep_success(conn, sess)
    sess = session_service.active_session(conn)
    assert sess.state == sm.STATE_SLEEP_SUCCESS

    # 6) 未到第二天不能结算
    with pytest.raises(RuleError):
        reward_service.settle(conn, sess.id)

    # 7) 模拟第二天 -> 结算奖励
    session_service.demo_next_day(conn)
    reward = reward_service.settle(conn, sess.id)
    assert reward["coins"] == 10
    assert reward["streak_days"] == 1
    assert reward["total_coins"] == 10

    # 幂等：重复结算返回 already
    reward2 = reward_service.settle(conn, sess.id)
    assert reward2["already"] is True

    # 8) 会话已终结（REWARD），历史可查
    assert session_service.active_session(conn) is None
    history = session_service.history(conn)
    assert len(history) == 1
    assert history[0]["coins"] == 10


def test_ready_scenario_jumps_to_sleep(conn):
    _goto_window(conn)
    sess = session_service.start_session(conn)
    intervention_service.start_flow(conn, sess, "ready", content_type="story")
    sess = session_service.active_session(conn)
    assert sess.state == sm.STATE_SLEEP_MODE
    assert sess.content_type == "story"


def test_no_content_means_quiet_sleep(conn):
    """用户不选择内容 -> 安静休息，不自动播放（设计原则：先询问再播放）。"""
    _goto_window(conn)
    sess = session_service.start_session(conn)
    intervention_service.start_flow(conn, sess, "ready")  # 未携带 content_type
    sess = session_service.active_session(conn)
    assert sess.state == sm.STATE_SLEEP_MODE
    assert sess.content_id is None


def test_working_scenario_stages(conn):
    _goto_window(conn)
    sess = session_service.start_session(conn)
    intervention_service.start_flow(conn, sess, "working")
    sess = session_service.active_session(conn)
    assert sess.state == sm.STATE_STAGE_1
    intervention_service.act(conn, sess, "prepare_sleep")
    sess = session_service.active_session(conn)
    assert sess.state == sm.STATE_SLEEP_MODE


def test_reset_demo(conn):
    _goto_window(conn)
    sess = session_service.start_session(conn)
    intervention_service.start_flow(conn, sess, "shorts")
    assert session_service.active_session(conn) is not None

    reset_demo_state(conn)
    assert session_service.active_session(conn) is None
    profile = session_service.get_profile(conn)
    assert profile.streak_days == 0 and profile.total_coins == 0
    assert not clock.is_demo_time(conn)


def test_consecutive_nights_and_duplicate_night(conn):
    """多夜连续：streak 逐夜 +1 且积分同步 +10；重复结算同一夜不重复计分。"""
    from datetime import date as Date

    def one_night(day: Date, expect_coins: int, expect_streak: int):
        target = clock.combine_date_hm(day, "23:00")
        clock.set_virtual_now(conn, target)
        sess = session_service.start_session(conn)
        intervention_service.start_flow(conn, sess, "ready", content_type="music")
        sess = session_service.active_session(conn)
        assert sess.date == day.strftime("%Y-%m-%d")
        base = clock.effective_now(conn)
        clock.set_virtual_now(conn, base + timedelta(minutes=60))
        intervention_service.check_sleep_success(conn, sess)
        session_service.demo_next_day(conn)
        reward = reward_service.settle(conn, sess.id)
        assert reward["coins"] == 10
        assert reward["total_coins"] == expect_coins
        assert reward["streak_days"] == expect_streak

    one_night(Date(2026, 9, 3), expect_coins=10, expect_streak=1)
    one_night(Date(2026, 9, 4), expect_coins=20, expect_streak=2)
    one_night(Date(2026, 9, 5), expect_coins=30, expect_streak=3)
    assert session_service.get_profile(conn).total_coins == 30
    assert session_service.get_profile(conn).streak_days == 3
    assert session_service.count_completed(conn) == 3

    # 重复结算同一个"夜晚"（模拟同一晚又演示一次）-> 不再加分
    dup_day = Date(2026, 9, 3)
    clock.set_virtual_now(conn, clock.combine_date_hm(dup_day, "23:00"))
    sess = session_service.start_session(conn)
    intervention_service.start_flow(conn, sess, "ready", content_type="story")
    sess = session_service.active_session(conn)
    base = clock.effective_now(conn)
    clock.set_virtual_now(conn, base + timedelta(minutes=60))
    intervention_service.check_sleep_success(conn, sess)
    session_service.demo_next_day(conn)
    reward = reward_service.settle(conn, sess.id)
    assert reward["already"] is True
    assert session_service.get_profile(conn).total_coins == 30
    assert session_service.get_profile(conn).streak_days == 3


def test_advance_and_refresh_resilience(conn):
    """推进虚拟时间 + 会话可由后端恢复（前端刷新页面场景）。"""
    _goto_window(conn)
    sess = session_service.start_session(conn)
    intervention_service.start_flow(conn, sess, "shorts")
    session_service.demo_advance(conn, 6)
    clock_now = clock.effective_now(conn)
    assert (clock_now.hour, clock_now.minute) == (23, 6)

    restored = session_service.active_session(conn)
    assert restored is not None and restored.id == sess.id
    assert restored.state == sm.STATE_STAGE_1
