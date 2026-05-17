from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.models.app_setting import AppSetting

DEFAULT_HOT_RATING_THRESHOLD = 4.5


class SettingsRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, key: str) -> Optional[str]:
        row = self.db.get(AppSetting, key)
        return row.value if row else None

    def get_float(self, key: str, default: float) -> float:
        raw = self.get(key)
        if raw is None:
            return default
        try:
            return float(raw)
        except ValueError:
            return default

    def set(self, key: str, value: str) -> AppSetting:
        row = self.db.get(AppSetting, key)
        if row is None:
            row = AppSetting(key=key, value=value)
            self.db.add(row)
        else:
            row.value = value
        return row

    def hot_rating_threshold(self) -> float:
        return self.get_float("hot_rating_threshold", DEFAULT_HOT_RATING_THRESHOLD)
