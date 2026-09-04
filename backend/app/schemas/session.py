"""Session / Demo 时间控制相关 Schema。"""
from __future__ import annotations

from pydantic import BaseModel, Field


class AdvanceIn(BaseModel):
    """虚拟时间前进（分钟）。"""

    minutes: int = Field(default=6, ge=1, le=1440, description="模拟前进的分钟数")
