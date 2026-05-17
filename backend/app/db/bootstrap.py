from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from app.config import settings
from app.database import engine

_ALEMBIC_INI = Path(__file__).resolve().parents[2] / "alembic.ini"


def _alembic_config() -> Config:
    cfg = Config(str(_ALEMBIC_INI))
    cfg.set_main_option("sqlalchemy.url", settings.database_url)
    return cfg


def init_database() -> None:
    """执行 Alembic 迁移至 head；兼容早期仅用 create_all 建表但未 stamp 的 SQLite 库。"""
    import app.models  # noqa: F401

    if settings.is_sqlite:
        db_path = settings.database_url.replace("sqlite:///", "", 1)
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    cfg = _alembic_config()
    insp = inspect(engine)

    if not insp.has_table("alembic_version"):
        if insp.has_table("users"):
            command.stamp(cfg, "head")
        else:
            command.upgrade(cfg, "head")
    else:
        command.upgrade(cfg, "head")
