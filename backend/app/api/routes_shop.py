"""积分兑换路由。"""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends

from ..db.database import get_db
from ..schemas.shop import RedeemIn
from ..services import shop_service

router = APIRouter(prefix="/api/shop", tags=["shop"])


@router.get("/items")
def items() -> dict:
    return {"items": shop_service.items()}


@router.post("/redeem")
def redeem(body: RedeemIn, conn: sqlite3.Connection = Depends(get_db)) -> dict:
    return shop_service.redeem(conn, body.item_id, body.custom_note)


@router.get("/orders")
def orders(conn: sqlite3.Connection = Depends(get_db)) -> dict:
    return {"items": shop_service.orders(conn)}
