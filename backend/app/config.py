from __future__ import annotations

from urllib.parse import quote_plus

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "酱菜交易平台 API"
    debug: bool = False
    # 完整连接串优先；未设置时由下方 POSTGRES_* 拼装（默认本地 PostgreSQL）
    database_url: str = ""
    postgres_host: str = "127.0.0.1"
    postgres_port: int = 5432
    postgres_user: str = "secondhand"
    postgres_password: str = "secondhand"
    postgres_db: str = "secondhand"
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7
    cors_origins: str = "http://127.0.0.1:5173,http://localhost:5173"
    seed_on_startup: bool = True

    # M5 — 本地 Ollama（LangChain 封装见 app.services.ai）
    ai_enabled: bool = True
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_chat_model: str = "qwen3.5:0.8b"
    ollama_embed_model: str = "mxbai-embed-large"
    ollama_vision_model: str = "qwen2.5vl:3b"
    ai_search_use_llm: bool = False
    ai_request_timeout_seconds: float = 30.0
    ai_search_timeout_seconds: float = 2.0
    ai_vision_timeout_seconds: float = 60.0
    # 识图上传：单张图片最大字节数（默认 5MB）
    ai_vision_max_image_bytes: int = 5 * 1024 * 1024
    ai_embed_batch_on_startup: bool = False
    # 对话加速：小库优先关键词；限制生成长度与历史轮数
    ai_chat_keyword_first: bool = True
    ai_chat_use_vector: bool = False
    ai_chat_max_history: int = 4
    ai_chat_num_predict: int = 320
    ollama_keep_alive: str = "15m"

    @model_validator(mode="after")
    def _ensure_database_url(self) -> "Settings":
        if not self.database_url.strip():
            user = quote_plus(self.postgres_user)
            password = quote_plus(self.postgres_password)
            url = (
                f"postgresql+psycopg://{user}:{password}"
                f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
            )
            object.__setattr__(self, "database_url", url)
        return self

    @property
    def is_postgresql(self) -> bool:
        return self.database_url.startswith("postgresql")

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


settings = Settings()
