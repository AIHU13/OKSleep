"""Mock 场景与助眠内容目录（静态数据，MVP 不接外部源）。"""
from __future__ import annotations

# ---- 当前状态（设计说明 §3.2 三种场景）----
SCENARIOS: dict[str, dict] = {
    "shorts": {
        "key": "shorts",
        "name": "正在刷短视频",
        "icon": "📱",
        "desc": "越刷越清醒，大脑被多巴胺牵着走",
        "family": "entertainment",
    },
    "working": {
        "key": "working",
        "name": "仍在工作 / 加班",
        "icon": "💻",
        "desc": "大脑高速运转，还没切换到休息状态",
        "family": "work",
    },
    "ready": {
        "key": "ready",
        "name": "已准备休息",
        "icon": "🛏️",
        "desc": "洗漱完毕，已经躺好准备入睡",
        "family": "relax",
    },
}

SCENARIO_KEYS: list[str] = list(SCENARIOS.keys())

# ---- 助眠内容目录 ----
# type: music 助眠音乐 / story 睡前故事 / noise 白噪音
CONTENTS: list[dict] = [
    {"id": 1, "type": "music", "title": "月光摇篮曲 · 钢琴版", "subtitle": "轻柔钢琴，缓慢心率", "duration_min": 10, "icon": "🎹", "mood": "calm"},
    {"id": 2, "type": "music", "title": "深海白噪音", "subtitle": "海底气泡的绵长呼吸", "duration_min": 15, "icon": "🌊", "mood": "ocean"},
    {"id": 3, "type": "noise", "title": "雨夜与壁炉", "subtitle": "雨声 + 柴火噼啪，天然白噪音", "duration_min": 12, "icon": "🌧️", "mood": "rain"},
    {"id": 4, "type": "story", "title": "月亮邮差", "subtitle": "治愈系短篇 · 今晚的收件人是你", "duration_min": 8, "icon": "🌙", "mood": "gentle"},
    {"id": 5, "type": "story", "title": "山间的风", "subtitle": "温柔入梦故事 · 把烦恼留在山下", "duration_min": 9, "icon": "🏔️", "mood": "gentle"},
    {"id": 6, "type": "story", "title": "星尘旅店", "subtitle": "慢节奏长篇 · 陪你在星海里打烊", "duration_min": 12, "icon": "✨", "mood": "dreamy"},
]

# 按偏好取推荐内容时用的候选分组
CONTENT_TYPE_POOL: dict[str, list[int]] = {
    "music": [1, 2, 3],
    "story": [4, 5, 6],
    "noise": [3],
}


def get_content(cid: int) -> dict | None:
    for item in CONTENTS:
        if item["id"] == cid:
            return dict(item)
    return None


def list_contents() -> list[dict]:
    return [dict(item) for item in CONTENTS]
