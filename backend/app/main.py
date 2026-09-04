"""OKSleep FastAPI 应用入口。

启动前会自动初始化 SQLite（data/oksleep.db）与种子数据。
RuleError 统一转换为带 code/message 的 HTTP 响应。
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api import (
    routes_agent,
    routes_deepnight,
    routes_demo,
    routes_reward,
    routes_session,
    routes_shop,
    routes_user,
    routes_work,
)
from .config import settings
from .db.init_db import init_db
from .services.errors import RuleError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("oksleep")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 幂等初始化：建表 + 种子数据
    init_db(settings.db_path)
    logger.info("数据库就绪: %s", settings.db_path)
    logger.info(
        "LLM 模式: %s（demo=Mock 文案；live=OpenAI 兼容接口）",
        settings.llm_mode,
    )
    yield


app = FastAPI(
    title="OKSleep API",
    description="睡前 30 分钟智能助眠 Agent（MVP / Demo）",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RuleError)
async def rule_error_handler(request: Request, exc: RuleError):
    return JSONResponse(
        status_code=exc.http_status,
        content={"detail": {"code": exc.code, "message": exc.message}},
    )


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "app": settings.app_name, "llm_mode": settings.llm_mode}


app.include_router(routes_user.router)
app.include_router(routes_session.router)
app.include_router(routes_agent.router)
app.include_router(routes_reward.router)
app.include_router(routes_demo.router)
app.include_router(routes_shop.router)
app.include_router(routes_deepnight.router)
app.include_router(routes_work.work_router)
app.include_router(routes_work.food_router)
