"""助眠内容服务：按用户偏好推荐（Mock 目录驱动）。"""
from __future__ import annotations

from ..mock.scenarios import CONTENT_TYPE_POOL, get_content, list_contents

# 内容类型的中文名（用于前端分组展示）
TYPE_LABELS = {"music": "助眠音乐", "story": "睡前故事", "noise": "自然白噪音"}


def featured_for(preferred: list[str] | None) -> dict:
    """按偏好顺序取第一篇推荐内容（进入睡眠模式的默认声音）。"""
    prefs = preferred or ["music", "story"]
    for t in prefs:
        pool = CONTENT_TYPE_POOL.get(t)
        if pool:
            item = get_content(pool[0])
            if item:
                return item
    return get_content(1)


def pick_by_type(content_type: str | None, preferred: list[str] | None = None) -> dict | None:
    """按用户显式选择返回内容；content_type 为空/未知 -> None（安静休息）。"""
    if content_type in ("music", "story", "noise"):
        pool = CONTENT_TYPE_POOL.get(content_type)
        if pool:
            return get_content(pool[0])
    # 未选择 -> 不自动播放；仍保留 AI 推荐能力说明（见前端标注）
    return None


def list_grouped(preferred: list[str] | None = None) -> dict:
    """按类型分组返回内容目录。"""
    grouped: dict[str, list[dict]] = {}
    for item in list_contents():
        grouped.setdefault(item["type"], []).append(item)
    return grouped
