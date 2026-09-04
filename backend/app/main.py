"""OKSleep FastAPI 应用入口。

启动前会自动初始化 SQLite（data/oksleep.db）与种子数据。
RuleError 统一转换为带 code/message 的 HTTP 响应。
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

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
from .config import ROOT_DIR, settings
from .db.init_db import init_db
from .services.errors import RuleError

# 前端产物目录（由 vite build 生成；存在时由本服务同源托管）
FRONTEND_DIST = ROOT_DIR / "frontend" / "dist"

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
    logger.info("公开演示模式(public_demo): %s", settings.public_demo)
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


@app.middleware("http")
async def docs_local_only(request: Request, call_next):
    """对外公开时：/docs /redoc /openapi.json 一律 403（仅限本机/非公开模式可看）。

    注意：隧道回源到本机后 client.host 恒为 127.0.0.1，因此公开模式下必须直接拒绝。
    """
    if request.url.path in ("/docs", "/redoc", "/openapi.json"):
        host = request.client.host if request.client else ""
        loopback = host in ("127.0.0.1", "::1", "localhost")
        if settings.public_demo or not loopback:
            return JSONResponse(status_code=403, content={"detail": "forbidden"})
    return await call_next(request)


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

# ---------------- 前端静态资源（同源单端口托管） ----------------
# 说明：/api/* 路由已在上方注册并优先匹配；此处仅托管构建产物并做 SPA 回退。
if (FRONTEND_DIST / "index.html").exists():
    if (FRONTEND_DIST / "assets").exists():
        app.mount(
            "/assets",
            StaticFiles(directory=str(FRONTEND_DIST / "assets")),
            name="assets",
        )
    if (FRONTEND_DIST / "videos").exists():
        app.mount(
            "/videos",
            StaticFiles(directory=str(FRONTEND_DIST / "videos")),
            name="videos",
        )

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        # 未知路径统一回退到应用入口（React SPA 前端路由）
        return FileResponse(FRONTEND_DIST / "index.html")
