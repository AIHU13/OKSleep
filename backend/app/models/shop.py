"""积分兑换订单。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

SHOP_ORDER_TABLE = "shop_orders"

SHOP_ORDER_DDL = """
CREATE TABLE IF NOT EXISTS shop_orders (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL,
    item_id      INTEGER NOT NULL,
    item_name    TEXT    NOT NULL,
    item_icon    TEXT,
    coins_spent  INTEGER NOT NULL,
    date         TEXT    NOT NULL,
    status       TEXT    NOT NULL DEFAULT 'delivering',
    created_at   TEXT    NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_shop_orders_user ON shop_orders (user_id);
"""


@dataclass
class ShopOrder:
    id: int
    user_id: int
    item_id: int
    item_name: str
    item_icon: Optional[str] = None
    coins_spent: int = 0
    date: str = ""
    status: str = "delivering"
    created_at: str = ""

    @staticmethod
    def from_row(row) -> "ShopOrder":
        return ShopOrder(
            id=row["id"],
            user_id=row["user_id"],
            item_id=row["item_id"],
            item_name=row["item_name"],
            item_icon=row["item_icon"],
            coins_spent=row["coins_spent"],
            date=row["date"],
            status=row["status"],
            created_at=row["created_at"],
        )
