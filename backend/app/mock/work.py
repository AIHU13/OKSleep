"""工作型 / 服务型 Agent Mock：任务目录、结果模板与外卖配送状态。"""
from __future__ import annotations

# 深夜计划：工作型 Agent 可委托任务（Mock 演示，后续替换为真实 Agent 能力）
WORK_TASK_TYPES: list[dict] = [
    {
        "key": "summary",
        "name": "数据汇总",
        "icon": "📊",
        "desc": "自动汇总今日数据并整理成摘要表",
        "duration_min": 6,
        "result": "数据汇总已完成：今日关键指标 12 项已整理成摘要表，明早可直接使用 ✅",
    },
    {
        "key": "report",
        "name": "报告整理",
        "icon": "📑",
        "desc": "按模板自动整理成完整报告初稿",
        "duration_min": 8,
        "result": "报告整理已完成：5 个章节初稿已按模板补齐，标出 2 处需你确认 ✅",
    },
    {
        "key": "ppt",
        "name": "PPT 生成",
        "icon": "🖥️",
        "desc": "基于素材自动生成演示文稿初稿（约 10 页）",
        "duration_min": 10,
        "result": "PPT 已生成：10 页初稿含图表与讲稿备注，明早可快速润色 ✅",
    },
]

TASK_KEY_TO_TYPE: dict[str, dict] = {t["key"]: t for t in WORK_TASK_TYPES}

# 外卖配送阶段（按虚拟时间推进）
FOOD_STAGES: list[dict] = [
    {"key": "placed", "label": "已下单", "msg": "订单已创建，正在为你联系商家…"},
    {"key": "accepted", "label": "商家接单", "msg": "商家已接单，正在备餐 🥐"},
    {"key": "pickup", "label": "骑手取餐", "msg": "骑手已取餐，正在配送 🛵"},
    {"key": "delivering", "label": "配送中", "msg": "快到你楼下啦，预计 5 分钟送达"},
    {"key": "delivered", "label": "已送达", "msg": "早餐已送达！趁热吃，元气满满 ☀️"},
]

# 到达下一阶段的累计分钟数（0/2/5/8/13 -> delivered）
FOOD_STAGE_AT_MIN = (0, 2, 5, 8, 13)
FOOD_TOTAL_MIN = 13

BREAKFAST_ITEM = {
    "id": 7,
    "name": "暖心早餐 · 配送套餐",
    "icon": "🥐",
    "item_name": "暖心早餐（豆浆 + 三明治）",
}
