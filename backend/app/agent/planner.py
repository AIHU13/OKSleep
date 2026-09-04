"""Agent Planner：LLM 文案生成编排（规范第 9 条：失败自动回退 Mock 策略）。

架构说明（规范 §4）：
    Agent Planner --(live)--> LLM API (OpenAI 兼容)
                   `--(demo/fail)--> Mock LLM（policy.mock_intervention）

demo 模式（默认）：不配置 Key，planner 直接走 Mock；配置 Key 且 LLM_MODE=live 时，
调用 OpenAI 兼容接口并做 Schema 校验，失败自动回退，保证演示永不中断。
"""
from __future__ import annotations

import logging
from typing import Optional

from ..config import settings
from .policy import PolicyContext, mock_intervention
from .prompt import SYSTEM_PROMPT, AgentMessage, build_user_prompt, parse_agent_message

logger = logging.getLogger(__name__)


class Planner:
    """干预文案生成器。线程安全（每次生成独立 client 调用）。"""

    def __init__(self, llm_enabled: Optional[bool] = None):
        self._llm_enabled = settings.llm_enabled if llm_enabled is None else llm_enabled

    # ------------------------------------------------------------------
    def generate(self, ctx: PolicyContext) -> dict:
        """返回 {text, suggestion, source}；source ∈ {llm, mock}。"""
        if self._llm_enabled:
            message = self._try_llm(ctx)
            if message is not None:
                return {"text": message.text, "suggestion": message.suggestion, "source": "llm"}
        mock = mock_intervention(ctx)
        return {"text": mock["text"], "suggestion": mock.get("suggestion", ""), "source": "mock"}

    def _try_llm(self, ctx: PolicyContext) -> Optional[AgentMessage]:
        """调用 OpenAI 兼容接口；超时/异常/Schema 不合法都返回 None。"""
        try:
            from openai import OpenAI

            client = OpenAI(
                base_url=settings.openai_base_url or None,
                api_key=settings.openai_api_key,
                timeout=settings.llm_timeout,
                max_retries=0,
            )
            payload = {
                "scenario": ctx.scenario,
                "state": ctx.state,
                "stage": ctx.stage,
                "bedtime": ctx.bedtime,
                "wake_time": ctx.wake,
                "now_phase": ctx.phase_text,
                "streak_days": ctx.streak_days,
                "recommended_content": (
                    ctx.featured_content if ctx.featured_content else None
                ),
                "today": ctx.now.strftime("%Y-%m-%d %H:%M"),
            }
            resp = client.chat.completions.create(
                model=settings.llm_model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": build_user_prompt(payload)},
                ],
                response_format={"type": "json_object"},
                temperature=0.9,
                max_tokens=settings.llm_max_tokens,
            )
            raw = resp.choices[0].message.content or ""
            return parse_agent_message(raw)
        except Exception as exc:  # 网络 / 鉴权 / 超时 / 解析失败 → 回退
            logger.warning("LLM 调用失败，回退 Mock 策略: %s", exc)
            return None


planner = Planner()
