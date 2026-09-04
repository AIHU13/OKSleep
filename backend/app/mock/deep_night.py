"""深夜计划任务目录：类型、规范文档（Mock）与交付物模板。

用于首页「表格配置」、Stage 3「一键启动」与次日「交付看板」的展示说明；
接入真实工作型/服务型 Agent 后替换为真实执行与交付。
"""
from __future__ import annotations

# 分类
CATEGORIES: list[dict] = [
    {"key": "daily", "name": "日常任务"},
    {"key": "work", "name": "工作任务"},
]

# 任务类型目录（含参数说明）
TASK_TYPES: list[dict] = [
    {
        "key": "breakfast",
        "category": "daily",
        "name": "预定早餐",
        "icon": "🥐",
        "desc": "指定配送时间，服务 Agent 明早自动下单配送到家",
        "params": [
            {"key": "deliver_at", "label": "期望配送时间", "type": "time", "default": "07:40"},
            {"key": "note", "label": "备注（可选）", "type": "text", "default": ""},
        ],
    },
    {
        "key": "remind",
        "category": "daily",
        "name": "明早提醒事项",
        "icon": "⏰",
        "desc": "把重要事项交给 Agent，明早按时提醒你",
        "params": [
            {"key": "note", "label": "提醒内容", "type": "text", "default": "记得带会议材料"},
        ],
    },
    {
        "key": "weekly_report",
        "category": "work",
        "name": "周报撰写",
        "icon": "📝",
        "desc": "在工作区中按规范文档自动撰写本周周报",
        "params": [
            {"key": "workspace", "label": "工作区", "type": "text", "default": "数据中台 · 周会工作区"},
            {"key": "spec_doc", "label": "工作规范与要求文档", "type": "spec", "default": "weekly_v2"},
        ],
    },
    {
        "key": "ppt",
        "category": "work",
        "name": "PPT 制作",
        "icon": "🖥️",
        "desc": "在工作区按演示规范生成汇报 PPT 初稿",
        "params": [
            {"key": "workspace", "label": "工作区", "type": "text", "default": "增长分析 · 工作区"},
            {"key": "topic", "label": "主题（可选）", "type": "text", "default": "Q3 用户增长复盘"},
            {"key": "spec_doc", "label": "工作规范与要求文档", "type": "spec", "default": "presentation"},
        ],
    },
]

TASK_TYPE_BY_KEY: dict[str, dict] = {t["key"]: t for t in TASK_TYPES}

# 规范 / 要求说明文档（工作 Agent 执行时参照）
SPEC_DOCS: list[dict] = [
    {
        "key": "weekly_v2",
        "name": "《周报规范 v2》",
        "summary": "要求：本周完成/进展/风险/下周计划四段式；数据口径与看板一致；上限 500 字",
    },
    {
        "key": "presentation",
        "name": "《演示汇报规范》",
        "summary": "要求：结论先行；每页 ≤ 3 个要点；配 1 张图表；含讲稿备注；页数 8-12",
    },
]

SPEC_DOC_BY_KEY: dict[str, dict] = {d["key"]: d for d in SPEC_DOCS}

# 若未预先配置，Stage 3 一键启动时的默认任务（便于直接演示）
DEFAULT_ACTIVATION_TASKS: list[dict] = [
    {
        "category": "daily",
        "task_type": "breakfast",
        "title": "预定早餐",
        "params": {"deliver_at": "07:40", "note": ""},
    },
    {
        "category": "work",
        "task_type": "weekly_report",
        "title": "周报撰写",
        "params": {"workspace": "数据中台 · 周会工作区", "spec_doc": "weekly_v2"},
    },
    {
        "category": "work",
        "task_type": "ppt",
        "title": "PPT 制作",
        "params": {
            "workspace": "增长分析 · 工作区",
            "topic": "Q3 用户增长复盘",
            "spec_doc": "presentation",
        },
    },
]

# 工作任务执行时长（分钟，均在"入睡 1 小时"内完成，便于演示推进）
WORK_DURATION_MIN = {"weekly_report": 20, "ppt": 30, "summary": 15, "report": 18}


# --------------------------------------------------------------------------
# 交付物模板（次日"点击查看"展示用，Mock 文本）
# --------------------------------------------------------------------------

def weekly_report_artifact(topic: str = "本周工作") -> dict:
    return {
        "kind": "weekly_report",
        "title": f"{topic} · 本周周报",
        "body": (
            "# 本周工作周报\n\n"
            "## 一、本周完成\n"
            "- 数据看板接口联调完成并上线（D-101 需求已交付）\n"
            "- 增长漏斗分析报告产出，关键指标口径与看板一致\n\n"
            "## 二、进展与风险\n"
            "- 转化率周环比 +3.2%，符合预期\n"
            "- 风险：报表查询高峰延迟偏高，已列入下周优化\n\n"
            "## 三、下周计划\n"
            "- 慢查询治理上线；输出月度复盘初稿\n\n"
            "（由深夜工作 Agent 按《周报规范 v2》自动撰写，已标注待你确认项 2 处）"
        ),
    }


def ppt_artifact(topic: str) -> dict:
    return {
        "kind": "ppt",
        "title": f"《{topic}.pptx》",
        "body": (
            f"PPT 已按《演示汇报规范》生成，共 10 页，含讲稿备注：\n\n"
            "1. 封面：{topic}\n"
            "2. 业务概览 · 核心数据一页图\n"
            "3. 关键指标趋势（含图表）\n"
            "4. 归因分析：渠道 / 产品 / 时间\n"
            "5. 亮点与问题\n"
            "6. 下季度规划（3 个要点）\n"
            "…\n"
            "10. 附录：口径说明\n\n"
            "（每页均配有讲稿备注，明早可快速润色后直接汇报）"
        ),
    }


def breakfast_artifact(deliver_at: str, note: str = "") -> dict:
    return {
        "kind": "breakfast",
        "title": "暖心早餐 · 配送",
        "body": (
            "🥐 暖心早餐套餐：豆浆 + 三明治\n"
            f"⏰ 期望配送时间：明早 {deliver_at}\n"
            f"📝 备注：{note or '无'}\n"
            "状态：由早餐服务 Agent 自动下单，配送到家"
        ),
    }


def remind_artifact(note: str) -> dict:
    return {
        "kind": "remind",
        "title": "明早提醒",
        "body": f"⏰ 已设置明早提醒：{note}",
    }
