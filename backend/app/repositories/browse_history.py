from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.browse_history import BrowseHistory


class BrowseHistoryRepository:
    MAX_ROWS = 100

    def __init__(self, db: Session) -> None:
        self.db = db

    def record(self, user_id: int, product_id: int) -> None:
        stmt = select(BrowseHistory).where(
            BrowseHistory.user_id == user_id,
            BrowseHistory.product_id == product_id,
        )
        row = self.db.scalars(stmt).first()
        now = datetime.now(timezone.utc)
        if row:
            row.viewed_at = now
        else:
            self.db.add(BrowseHistory(user_id=user_id, product_id=product_id, viewed_at=now))
        self.db.commit()
        self._trim(user_id)

    def _trim(self, user_id: int) -> None:
        stmt = (
            select(BrowseHistory.id)
            .where(BrowseHistory.user_id == user_id)
            .order_by(BrowseHistory.viewed_at.desc())
        )
        ids = [r for r in self.db.scalars(stmt).all()]
        if len(ids) <= self.MAX_ROWS:
            return
        drop = ids[self.MAX_ROWS :]
        self.db.execute(delete(BrowseHistory).where(BrowseHistory.id.in_(drop)))
        self.db.commit()

    def recent_product_ids(self, user_id: int, limit: int = 10) -> list[int]:
        stmt = (
            select(BrowseHistory.product_id)
            .where(BrowseHistory.user_id == user_id)
            .order_by(BrowseHistory.viewed_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())
