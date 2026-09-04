"""核心状态机与 Rule Engine（规范第 5/6/7 条：规则引擎负责可控）。

状态流（设计说明 §3.3）：
    IDLE -> BEDTIME_START -> STAGE_1/2/3 -> SLEEP_MODE -> SLEEP_SUCCESS -> REWARD

时间常量：
    BEDTIME_WINDOW_MIN = 30  （睡前 30 分钟窗口）
    SLEEP_SUCCESS_MINUTES = 60（模拟 1 小时未使用手机即成功）
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

from ..clock import combine_date_hm, minutes_to_hm

# ---- 状态常量 ----
STATE_IDLE = "IDLE"
STATE_BEDTIME_START = "BEDTIME_START"
STATE_STAGE_1 = "STAGE_1"
STATE_STAGE_2 = "STAGE_2"
STATE_STAGE_3 = "STAGE_3"
STATE_SLEEP_MODE = "SLEEP_MODE"
STATE_SLEEP_SUCCESS = "SLEEP_SUCCESS"
STATE_REWARD = "REWARD"

# 主链状态顺序（用于前端步骤条展示）
MAIN_FLOW: list[str] = [
    STATE_BEDTIME_START,
    STATE_STAGE_1,
    STATE_STAGE_2,
    STATE_STAGE_3,
    STATE_SLEEP_MODE,
    STATE_SLEEP_SUCCESS,
    STATE_REWARD,
]

STAGE_LABELS = {
    STATE_STAGE_1: "Stage 1 · 温和提醒",
    STATE_STAGE_2: "Stage 2 · 引导切换",
    STATE_STAGE_3: "Stage 3 · 明日日程提醒",
}

TERMINAL_STATES: set[str] = {STATE_REWARD}

# 合法状态转移表（Rule Engine 核心）
ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    STATE_IDLE: {STATE_BEDTIME_START},
    STATE_BEDTIME_START: {STATE_STAGE_1, STATE_SLEEP_MODE},
    STATE_STAGE_1: {STATE_STAGE_2, STATE_SLEEP_MODE},
    STATE_STAGE_2: {STATE_STAGE_3, STATE_SLEEP_MODE},
    STATE_STAGE_3: {STATE_SLEEP_MODE},
    STATE_SLEEP_MODE: {STATE_SLEEP_SUCCESS},
    STATE_SLEEP_SUCCESS: {STATE_REWARD},
    STATE_REWARD: set(),
}

# 业务常量
BEDTIME_WINDOW_MIN = 30
SLEEP_SUCCESS_MINUTES = 60
COINS_PER_SUCCESS = 10


def is_valid_state(state: str) -> bool:
    return state in ALLOWED_TRANSITIONS


def can_transition(current: str, target: str) -> bool:
    """Rule Engine：状态转移是否合法。"""
    return current in ALLOWED_TRANSITIONS and target in ALLOWED_TRANSITIONS[current]


def is_terminal(state: str) -> bool:
    return state in TERMINAL_STATES


def stage_number(state: str) -> int | None:
    """STAGE_k -> k；非干预态返回 None。"""
    if state in (STATE_STAGE_1, STATE_STAGE_2, STATE_STAGE_3):
        return int(state.rsplit("_", 1)[1])
    return None


def state_from_stage(stage: int) -> str:
    return f"STAGE_{stage}"


def is_weekend(day: date) -> bool:
    return day.weekday() >= 5  # 5=周六, 6=周日


def bedtime_hm(profile, day: date) -> str:
    """当日入睡时间（工作日/周末不同作息）。"""
    return profile.weekend_bedtime if is_weekend(day) else profile.weekday_bedtime


def wake_hm(profile, day: date) -> str:
    return profile.weekend_wake if is_weekend(day) else profile.weekday_wake


def bedtime_datetime(profile, day: date) -> datetime:
    return combine_date_hm(day, bedtime_hm(profile, day))


def wake_datetime(profile, day: date) -> datetime:
    """入睡日对应的起床时刻：若起床时间早于入睡则视为次日。"""
    bed = bedtime_datetime(profile, day)
    wake = combine_date_hm(day, wake_hm(profile, day))
    if wake <= bed:
        wake = combine_date_hm(day + timedelta(days=1), wake_hm(profile, day))
    return wake


def window_start(profile, day: date) -> datetime:
    """睡前 30 分钟 = 助眠流程开始时间（T-30）。"""
    return bedtime_datetime(profile, day) - timedelta(minutes=BEDTIME_WINDOW_MIN)


def phase_of(profile, now: datetime) -> dict:
    """时间规则：now 相对用户作息处于哪个相位。

    返回 dict：phase 与展示文本。
    相位：
      - morning_after : 今日起床前（昨夜睡眠尚未结束/新的一天）
      - before_window : 尚未到睡前 30 分钟窗口
      - in_window     : 窗口内（T-30 ~ 入睡）
      - late          : 已超过目标入睡时间
    """
    day = now.date()
    bed = bedtime_datetime(profile, day)
    window = window_start(profile, day)
    # 昨晚入睡对应的今晨起床时刻
    wake_prev = wake_datetime(profile, day - timedelta(days=1))

    if now < wake_prev:
        phase = "morning_after"
    elif now >= window and now < bed:
        phase = "in_window"
    elif now >= bed:
        phase = "late"
    else:
        phase = "before_window"

    return {
        "phase": phase,
        "window_start": window,
        "bedtime": bed,
        "wake": wake_prev,
        "phase_text": _phase_text(phase, now, bed, wake_prev, window),
    }


def phase_text_of(profile, now: datetime) -> str:
    """便捷取文本。"""
    return phase_of(profile, now)["phase_text"]


def _phase_text(phase: str, now: datetime, bed: datetime, wake: datetime, window: datetime) -> str:
    if phase == "in_window":
        return "已经进入睡前 30 分钟窗口 🌙"
    if phase == "late":
        return "已经超过目标入睡时间，是时候休息了"
    if phase == "morning_after":
        return "新的一天开始了，早安 ☀️"
    # before_window：计算距离窗口还有多久
    total_min = max(0, int((window - now).total_seconds() // 60))
    return f"距离睡前窗口还有 {minutes_to_hm(total_min)}（目标 {bed:%H:%M} 入睡）"
