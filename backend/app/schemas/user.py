"""用户作息相关 Schema。"""
from __future__ import annotations

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

HM_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def _check_hm(v: str) -> str:
    if not HM_RE.match(v or ""):
        raise ValueError("时间格式必须为 HH:MM")
    return v


class ProfileUpdateIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    weekday_bedtime: str | None = Field(default=None)
    weekday_wake: str | None = Field(default=None)
    weekend_bedtime: str | None = Field(default=None)
    weekend_wake: str | None = Field(default=None)
    preferred_content: list[str] | None = Field(
        default=None, description='如 ["music", "story"]'
    )

    _bed = field_validator(
        "weekday_bedtime", "weekday_wake", "weekend_bedtime", "weekend_wake"
    )(_check_hm)

    @field_validator("preferred_content")
    @classmethod
    def _content(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return None
        allowed = {"music", "story", "noise"}
        cleaned = [t for t in v if t in allowed]
        if not cleaned:
            raise ValueError("preferred_content 必须包含 music/story/noise 中的至少一项")
        return cleaned


class OnboardingIn(BaseModel):
    """首次启动配置向导完成标记。"""

    done: bool = True
