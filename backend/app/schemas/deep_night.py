"""深夜计划 Schema。"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class PlanTaskIn(BaseModel):
    category: str = Field(description="daily | work")
    task_type: str = Field(description="breakfast | remind | weekly_report | ppt")
    title: Optional[str] = Field(default=None)
    params: dict = Field(default_factory=dict)


class PlanConfigIn(BaseModel):
    tasks: list[PlanTaskIn] = Field(default_factory=list)


class ActivateIn(BaseModel):
    session_id: int
