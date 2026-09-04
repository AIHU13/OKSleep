"""Rule Engine 状态机规则测试（不依赖 DB）。"""
from datetime import datetime

from app.agent import state as sm
from app.models.user import UserProfile


def _profile() -> UserProfile:
    return UserProfile(
        id=1,
        weekday_bedtime="23:30",
        weekday_wake="07:30",
        weekend_bedtime="23:30",
        weekend_wake="07:30",
    )


def test_transition_table():
    assert sm.can_transition(sm.STATE_IDLE, sm.STATE_BEDTIME_START)
    assert sm.can_transition(sm.STATE_BEDTIME_START, sm.STATE_STAGE_1)
    assert sm.can_transition(sm.STATE_BEDTIME_START, sm.STATE_SLEEP_MODE)
    assert sm.can_transition(sm.STATE_STAGE_1, sm.STATE_STAGE_2)
    assert sm.can_transition(sm.STATE_STAGE_2, sm.STATE_STAGE_3)
    assert sm.can_transition(sm.STATE_STAGE_3, sm.STATE_SLEEP_MODE)
    assert sm.can_transition(sm.STATE_SLEEP_MODE, sm.STATE_SLEEP_SUCCESS)
    assert sm.can_transition(sm.STATE_SLEEP_SUCCESS, sm.STATE_REWARD)


def test_illegal_transitions():
    # 不存在 / 非法的目标状态
    assert not sm.can_transition(sm.STATE_STAGE_3, "STAGE_4")
    assert not sm.can_transition(sm.STATE_IDLE, sm.STATE_SLEEP_MODE)
    assert not sm.can_transition(sm.STATE_STAGE_1, sm.STATE_REWARD)
    assert not sm.can_transition(sm.STATE_REWARD, sm.STATE_IDLE)
    assert not sm.can_transition(sm.STATE_SLEEP_SUCCESS, sm.STATE_SLEEP_MODE)
    assert not sm.can_transition("UNKNOWN", sm.STATE_IDLE)


def test_terminal_and_stage():
    assert sm.is_terminal(sm.STATE_REWARD)
    assert not sm.is_terminal(sm.STATE_STAGE_2)
    assert sm.stage_number(sm.STATE_STAGE_2) == 2
    assert sm.stage_number(sm.STATE_SLEEP_MODE) is None


def test_phase_window_weekday():
    # 2026-09-03 是周四（工作日）
    now = datetime(2026, 9, 3, 23, 10)
    phase = sm.phase_of(_profile(), now)
    assert phase["phase"] == "in_window"
    assert phase["window_start"].strftime("%H:%M") == "23:00"


def test_phase_before_window():
    now = datetime(2026, 9, 3, 21, 0)
    phase = sm.phase_of(_profile(), now)
    assert phase["phase"] == "before_window"


def test_phase_late():
    now = datetime(2026, 9, 3, 23, 45)
    phase = sm.phase_of(_profile(), now)
    assert phase["phase"] == "late"


def test_phase_morning():
    now = datetime(2026, 9, 4, 7, 0)
    phase = sm.phase_of(_profile(), now)
    assert phase["phase"] == "morning_after"
