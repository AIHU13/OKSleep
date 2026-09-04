"""深夜计划（工作/服务 Agent）Schema。"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class WorkTaskStartIn(BaseModel):
    kind: str = Field(description="summary | report | ppt")
    session_id: Optional[int] = Field(default=None, description="缺省用当前活跃会话")


class FoodOrderIn(BaseModel):
    source: Literal["redeem_breakfast", "work_agent"] = "redeem_breakfast"
    item_name: Optional[str] = Field(default=None)
    note: Optional[str] = Field(default=None, max_length=60)
