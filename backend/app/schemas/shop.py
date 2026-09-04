"""积分兑换 Schema。"""
from __future__ import annotations

from pydantic import BaseModel, Field


class RedeemIn(BaseModel):
    item_id: int = Field(ge=1)
    custom_note: str | None = Field(default=None, max_length=60, description="自定义礼物的备注")
