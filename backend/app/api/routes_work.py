"""深夜计划路由：工作 Agent 任务 / 早餐外卖。"""
from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends

from ..db.database import get_db
from ..schemas.work import FoodOrderIn, WorkTaskStartIn
from ..services import work_service

# 工作 Agent（深夜计划任务）
work_router = APIRouter(prefix="/api/work", tags=["work"])


@work_router.get("/types")
def task_types() -> dict:
    return {"items": work_service.task_types()}


@work_router.post("/start")
def start_task(body: WorkTaskStartIn, conn: sqlite3.Connection = Depends(get_db)) -> dict:
    return work_service.start_work_task(conn, body.kind, body.session_id)


@work_router.get("/tasks")
def list_tasks(session_id: int, conn: sqlite3.Connection = Depends(get_db)) -> dict:
    return {"items": work_service.tasks(conn, session_id)}


# 服务 Agent（早餐外卖）
food_router = APIRouter(prefix="/api/food", tags=["food"])


@food_router.post("/order")
def order_food(body: FoodOrderIn, conn: sqlite3.Connection = Depends(get_db)) -> dict:
    return work_service.place_food_order(conn, body.source, body.note, body.item_name)


@food_router.get("/orders")
def list_food(conn: sqlite3.Connection = Depends(get_db)) -> dict:
    return {"items": work_service.food_orders(conn)}
