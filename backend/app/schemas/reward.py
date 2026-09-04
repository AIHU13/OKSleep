"""奖励相关 Schema。"""
from __future__ import annotations

from pydantic import BaseModel, Field


class SettleIn(BaseModel):
    """次日奖励结算（可选指定 session_id，缺省用活跃会话）。"""

    session_id: int | None = Field(default=None)


class MissIn(BaseModel):
    """助眠失败记录（手机场景模拟）。"""

    scenario: str | None = Field(default="shorts")
    note: str | None = Field(default=None, max_length=60)
