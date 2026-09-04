"""Agent（干预）相关 Schema。"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, field_validator

# 进入睡眠时是否播放助眠内容：music 助眠音乐 / story 睡前故事 / noise 白噪音 / none=安静休息
CONTENT_TYPE_CHOICES = ("music", "story", "noise")


def normalize_content_type(v: Optional[str]) -> Optional[str]:
    """内容类型归一化：None/'none'/空 -> None（不自动播放）。"""
    if v is None:
        return None
    v = v.strip().lower()
    if v in ("", "none", "null", "quiet"):
        return None
    if v not in CONTENT_TYPE_CHOICES:
        raise ValueError("content_type 必须是 music / story / noise / none")
    return v


class ScenarioStartIn(BaseModel):
    """开始助眠时选择当前状态（设计说明 §3.2 三种场景）。

    content_type 仅在 scenario=ready（直接入睡）时生效；
    其余场景在分阶段干预结束、用户选择入睡时再指定。
    """

    scenario: str = Field(description="shorts | working | ready")
    content_type: Optional[str] = Field(
        default=None,
        description="进入睡眠后想听的内容：music/story/noise/none（缺省=不自动播放）",
    )

    @field_validator("content_type")
    @classmethod
    def _content_type(cls, v: Optional[str]) -> Optional[str]:
        return normalize_content_type(v)


class ActIn(BaseModel):
    """用户行为。

    prepare_sleep 时可携带 content_type 表达「想听什么入睡」；
    不携带表示安静休息（不自动播放任何内容）。
    """

    action: str = Field(description="continue | prepare_sleep")
    content_type: Optional[str] = Field(default=None)

    @field_validator("content_type")
    @classmethod
    def _content_type(cls, v: Optional[str]) -> Optional[str]:
        return normalize_content_type(v)
