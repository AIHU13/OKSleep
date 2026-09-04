"""积分兑换服务：商品目录 / 兑换（扣减积分）/ 订单历史。

规则：积分仅用于激励，兑换不重置连续打卡；积分不足拒绝兑换。
"""
from __future__ import annotations

import sqlite3

from ..clock import fmt, now_dt
from ..config import settings
from ..db.database import execute, query_all
from ..mock.shop import get_product, list_products
from ..models.shop import SHOP_ORDER_TABLE
from ..models.user import USER_PROFILE_TABLE
from .errors import RuleError


def items() -> list[dict]:
    return list_products()


def redeem(conn: sqlite3.Connection, item_id: int, custom_note: str | None = None) -> dict:
    product = get_product(item_id)
    if not product:
        raise RuleError("商品不存在", code="bad_item", http_status=404)

    row = conn.execute(
        f"SELECT total_coins FROM {USER_PROFILE_TABLE} WHERE id = ?",
        (settings.demo_user_id,),
    ).fetchone()
    coins = row["total_coins"] if row else 0
    price = product["price_coins"]
    if coins < price:
        raise RuleError(
            f"积分不足：还差 {price - coins} Sleep Coins（当前 {coins}）",
            code="insufficient_coins",
        )

    if product.get("custom"):
        name = custom_note or product["name"]
    else:
        name = product["name"]

    oid = execute(
        conn,
        f"""INSERT INTO {SHOP_ORDER_TABLE}
            (user_id, item_id, item_name, item_icon, coins_spent, date, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'delivering', ?)""",
        (
            settings.demo_user_id,
            product["id"],
            name,
            product.get("icon"),
            price,
            fmt(now_dt())[:10],
            fmt(now_dt()),
        ),
    )
    conn.execute(
        f"UPDATE {USER_PROFILE_TABLE} SET total_coins = total_coins - ? WHERE id = ?",
        (price, settings.demo_user_id),
    )
    conn.commit()

    return {
        "id": oid,
        "item_id": product["id"],
        "item_name": name,
        "item_icon": product.get("icon"),
        "coins_spent": price,
        "coins_left": coins - price,
        "status": "delivering",
        "message": f"兑换成功！《{name}》正在派送中，好好睡觉等它到吧 🎁",
    }


def orders(conn: sqlite3.Connection, limit: int = 20) -> list[dict]:
    rows = query_all(
        conn,
        f"SELECT * FROM {SHOP_ORDER_TABLE} WHERE user_id = ? ORDER BY id DESC LIMIT ?",
        (settings.demo_user_id, int(limit)),
    )
    return [
        {
            "id": r["id"],
            "item_name": r["item_name"],
            "item_icon": r["item_icon"],
            "coins_spent": r["coins_spent"],
            "date": r["date"],
            "status": r["status"],
        }
        for r in rows
    ]
