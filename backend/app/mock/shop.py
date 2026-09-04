"""积分兑换 Mock 商品目录（模拟展示，后续可替换为真实内容）。"""
from __future__ import annotations

SHOP_PRODUCTS: list[dict] = [
    {
        "id": 1,
        "name": "迪士尼保温杯 · 星空款",
        "brand": "Disney 官方",
        "desc": "睡前一杯温水，守护你的晚安时刻",
        "icon": "☕",
        "price_coins": 200,
        "tag": "好物",
        "stock": 9,
    },
    {
        "id": 2,
        "name": "迪士尼保温杯 · 小熊维尼",
        "brand": "Disney 官方",
        "desc": "温润配色 + 大容量，通勤助眠两相宜",
        "icon": "🍯",
        "price_coins": 260,
        "tag": "好物",
        "stock": 5,
    },
    {
        "id": 3,
        "name": "助眠香薰礼盒 · 薰衣草",
        "brand": "OKSleep × 香氛",
        "desc": "睡前 15 分钟点燃，营造安稳氛围",
        "icon": "🕯️",
        "price_coins": 320,
        "tag": "助眠",
        "stock": 12,
    },
    {
        "id": 4,
        "name": "星夜记忆枕",
        "brand": "OKSleep 甄选",
        "desc": "慢回弹护颈枕，好眠从好枕头开始",
        "icon": "🛌",
        "price_coins": 680,
        "tag": "助眠",
        "stock": 3,
    },
    {
        "id": 5,
        "name": "华为 Mate X6 · 睡眠激励款",
        "brand": "HUAWEI",
        "desc": "年度旗舰折叠屏，规律作息攒够积分就带它回家",
        "icon": "📱",
        "price_coins": 5000,
        "tag": "心愿",
        "stock": 1,
    },
    {
        "id": 6,
        "name": "自定义心愿礼盒",
        "brand": "定制",
        "desc": "写下一个想送自己的礼物，兑换后由你决定内容",
        "icon": "🎁",
        "price_coins": 100,
        "tag": "心愿",
        "stock": 99,
        "custom": True,
    },
    {
        "id": 7,
        "name": "暖心早餐 · 配送套餐",
        "brand": "早餐服务 Agent",
        "desc": "10 积分兑换暖心早餐，支持一键自动下单外卖配送",
        "icon": "🥐",
        "price_coins": 10,
        "tag": "服务",
        "stock": 999,
        "kind": "breakfast",
    },
]


def get_product(item_id: int) -> dict | None:
    for p in SHOP_PRODUCTS:
        if p["id"] == item_id:
            return dict(p)
    return None


def list_products() -> list[dict]:
    return [dict(p) for p in SHOP_PRODUCTS]
