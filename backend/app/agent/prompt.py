"""LLM Prompt 与输出 Schema（规范第 8 条：LLM 输出必须经过 Schema 校验）。"""
from __future__ import annotations

import json

from pydantic import BaseModel, Field, field_validator

SYSTEM_PROMPT = (
    "你是 SleepFlow 的睡前助眠 Agent，负责在用户睡前 30 分钟窗口内进行循循善诱的干预。\n"
    "铁律：\n"
    "1. 绝不提供医疗诊断或治疗建议。\n"
    "2. 只输出一个 JSON 对象，不要任何解释或 Markdown。\n"
    "3. 语气温柔、克制、不说教，像一位靠谱的朋友。\n"
    "4. 结合给出的用户作息与当前阶段生成文案，不编造用户没提供的日程。\n"
    "5. 文案控制在 120 字以内，建议（suggestion）控制在 40 字以内。\n"
)


def build_user_prompt(ctx: dict) -> str:
    """把策略上下文序列化为给 LLM 的 JSON。ctx 由 planner 组装。"""
    return json.dumps(ctx, ensure_ascii=False)


class AgentMessage(BaseModel):
    """LLM 结构化输出（干预文案）。"""

    text: str = Field(description="对用户说的话", max_length=240)
    suggestion: str = Field(default="", description="一条简短实用的小建议", max_length=80)
    tone: str = Field(default="warm", description="语气标记")

    @field_validator("text", "suggestion")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        return (v or "").strip()

    @field_validator("suggestion")
    @classmethod
    def clamp_suggestion(cls, v: str) -> str:
        return v[:80]

    @field_validator("text")
    @classmethod
    def clamp_text(cls, v: str) -> str:
        return v[:240]


def parse_agent_message(raw: str) -> AgentMessage | None:
    """解析 LLM 返回的 JSON；任何异常/字段不符都返回 None（触发 Mock 回退）。"""
    try:
        data = json.loads(raw)
        if not isinstance(data, dict):
            return None
        return AgentMessage.model_validate(data)
    except Exception:
        return None
