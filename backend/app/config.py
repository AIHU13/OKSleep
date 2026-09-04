"""全局配置：读取仓库根目录 .env，所有密钥通过环境变量注入（规范第 19 条）。"""
from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# 仓库根目录：backend/app/config.py -> sleepflow/
ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT_DIR / "data"
DEFAULT_DB_PATH = DATA_DIR / "sleepflow.db"


class Settings(BaseSettings):
    """应用配置。

    环境变量前缀 SLEEPFLOW_，例如 SLEEPFLOW_LLM_MODE=demo。
    文件位于仓库根目录 .env。
    """

    model_config = SettingsConfigDict(
        env_prefix="SLEEPFLOW_",
        env_file=str(ROOT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ---- 运行 ----
    app_name: str = "SleepFlow"
    llm_mode: str = "demo"  # demo | live
    backend_port: int = 8000

    # ---- LLM（OpenAI 兼容接口；demo 模式无需 Key）----
    openai_base_url: str = ""
    openai_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    llm_timeout: float = 20.0
    llm_max_tokens: int = 320

    # ---- 数据 ----
    db_path: Path = DEFAULT_DB_PATH
    demo_user_id: int = 1

    # ---- CORS ----
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def llm_enabled(self) -> bool:
        """demo 模式或未配置 Key 时禁用真实 LLM（规范第 9 条自动回退 Mock）。"""
        return self.llm_mode.strip().lower() == "live" and bool(self.openai_api_key.strip())


settings = Settings()
