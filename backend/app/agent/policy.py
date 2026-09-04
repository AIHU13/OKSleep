"""策略引擎：根据（作息 + 时间 + 场景 + 阶段）给出干预文案与建议。

MVP 原则（规范第 7/9 条）：LLM 负责文案与建议；
本文件提供"Mock 策略"，即 LLM 不可用或失败时的确定性回退，
并为 Planner 提供结构化上下文（LLM 与 Mock 共用同一输入）。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from . import state as sm

# 明日日程 Mock：Stage 3 / 睡前收尾 时使用
TOMORROW_PLAN: list[dict] = [
    {"time": "07:30", "item": "起床 · 拉开窗帘晒太阳"},
    {"time": "09:00", "item": "工作 · 深度专注 2 小时"},
    {"time": "12:30", "item": "午餐 · 散步 20 分钟"},
    {"time": "19:30", "item": "运动 · 慢跑 / 拉伸"},
    {"time": "22:30", "item": "睡前准备 · 放下电子设备"},
]


@dataclass
class PolicyContext:
    """Planner / Mock 共用的策略上下文。"""

    profile: object
    now: datetime
    scenario: str
    state: str
    stage: int | None = None
    bedtime: str = ""
    wake: str = ""
    phase_text: str = ""
    featured_content: dict | None = None
    tomorrow_plan: list = field(default_factory=lambda: TOMORROW_PLAN)
    streak_days: int = 0
    history: list = field(default_factory=list)


# --------------------------------------------------------------------------
# Mock 文案（分场景 × 分阶段，确定性、可离线演示）
# --------------------------------------------------------------------------

def mock_intervention(pc: PolicyContext) -> dict:
    """返回 {text, suggestion}。"""
    scenario = pc.scenario
    stage = pc.stage
    bed = pc.bedtime or "23:30"
    wake = pc.wake or "07:30"
    content = pc.featured_content

    # 进入睡眠模式（ready 场景 / 各阶段选择入睡）
    if pc.state == sm.STATE_SLEEP_MODE:
        if content:
            return {
                "text": (
                    "今晚你做得很好 🌙 手机已经放下，剩下的交给声音。"
                    f"为你播放《{content['title']}》，闭上眼睛，跟着呼吸走，我在旁边陪着你。"
                ),
                "suggestion": "把屏幕亮度调到最低，音量放到 30% 左右刚刚好",
            }
        return {
            "text": "今晚你做得很好 🌙 闭上眼睛，跟着呼吸走，我在旁边陪着你。",
            "suggestion": "把屏幕亮度调到最低，音量放到 30% 左右刚刚好",
        }

    if scenario == "ready":
        return {
            "text": f"一切就绪。目标 {bed} 入睡，现在进入睡眠模式刚刚好 🌙",
            "suggestion": "选择一段喜欢的声音，让身体先于意识放松下来",
        }

    if scenario == "shorts":
        return _shorts_text(stage, bed, wake, content)
    if scenario == "working":
        return _working_text(stage, bed, wake)

    # 兜底
    return {
        "text": f"时间不早了，距离 {bed} 入睡越来越近，试着让节奏慢下来吧。",
        "suggestion": "深呼吸三次，把注意力从屏幕上移开",
    }


def _shorts_text(stage: int | None, bed: str, wake: str, content: dict | None) -> dict:
    if stage == 1:
        return {
            "text": (
                f"夜已深 🌙 离你的目标入睡时间（{bed}）越来越近了。"
                "短视频算法只会让你越刷越清醒——试着现在就锁屏一次，"
                "哪怕只是 10 秒钟的深呼吸，也算赢回今晚。"
            ),
            "suggestion": "蓝光会抑制褪黑素分泌，把手机放到伸手够不到的地方",
        }
    if stage == 2:
        title = content["title"] if content else "睡前故事"
        return {
            "text": (
                "还是舍不得放下吗？没关系，我们不必一步到位。"
                "从「被动刷」切换到「主动听」，让大脑换个频道："
                f"我已为你准备好《{title}》，躺下来把它当作入睡的信号。"
            ),
            "suggestion": "换成助眠音乐或睡前故事，比继续刷更容易滑入困意",
        }
    if stage == 3:
        return {
            "text": (
                f"再看看时间：已经超过 {bed} 了。明天 {wake} 还要起床，"
                "再刷 10 分钟，明早就要多付 10 分钟的代价。"
                "今晚的娱乐时间，先到这里收工好吗？"
            ),
            "suggestion": "明天还有正事等你：见下方明日日程，睡饱了才接得住",
        }
    return {"text": "放下手机，准备休息吧 🌙", "suggestion": ""}


def _working_text(stage: int | None, bed: str, wake: str) -> dict:
    if stage == 1:
        return {
            "text": (
                f"工作辛苦了。现在距离你的目标入睡时间（{bed}）只剩一小段窗口。"
                "最后 5 分钟，把没写完的收个尾、存好档——剩下的，明天交给清醒的自己。"
            ),
            "suggestion": "给大脑一个「关机仪式」：合上电脑、起身倒杯温水",
        }
    if stage == 2:
        return {
            "text": (
                "还想再干一会儿？明白，那我们就把这一段干净利落地干完。"
                "别硬扛重复劳动——数据汇总、报告初稿、PPT 骨架这类活，"
                "都可以先拆给「深夜工作 Agent」搭好，你只留最重要的判断。"
            ),
            "suggestion": "继续到下一阶段，可发起「深夜计划」委托工作型 Agent 自主执行",
        }
    if stage == 3:
        return {
            "text": (
                "今天辛苦啦，剩下的工作就交给我吧，保证完成任务！🌙 "
                "已经深夜了——把整理数据、报告初稿这类活儿委托给深夜工作 Agent，"
                "让它替你干完，你安心去睡，明早验收成果就好。"
            ),
            "suggestion": "下方「深夜计划」可发起：数据汇总 / 报告整理 / PPT 生成，或预定早餐外卖",
        }
    return {"text": "收工了，去准备休息吧 🌙", "suggestion": ""}


# --------------------------------------------------------------------------
# 面向 Planner 的结构化上下文
# --------------------------------------------------------------------------

def build_context(
    profile,
    now: datetime,
    scenario: str,
    state: str,
    stage: int | None = None,
    featured_content: dict | None = None,
    streak_days: int = 0,
    history: list | None = None,
) -> PolicyContext:
    from ..mock.scenarios import SCENARIOS
    from .state import bedtime_hm, phase_text_of, wake_hm

    day = now.date()
    scenario_name = SCENARIOS.get(scenario, {}).get("name", scenario)
    return PolicyContext(
        profile=profile,
        now=now,
        scenario=scenario,
        state=state,
        stage=stage,
        bedtime=bedtime_hm(profile, day),
        wake=wake_hm(profile, day),
        phase_text=f"{phase_text_of(profile, now)}（场景：{scenario_name}）",
        featured_content=featured_content,
        streak_days=streak_days,
        history=history or [],
    )
