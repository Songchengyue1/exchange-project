from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.review import Review


class ReviewRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_order_id(self, order_id: int) -> Optional[Review]:
        return self.db.scalar(select(Review).where(Review.order_id == order_id))

    def get_by_id(self, review_id: int) -> Optional[Review]:
        stmt = (
            select(Review)
            .where(Review.id == review_id)
            .options(selectinload(Review.buyer))
        )
        return self.db.scalars(stmt).first()

    def list_by_buyer(self, buyer_id: int) -> list[Review]:
        stmt = (
            select(Review)
            .where(Review.buyer_id == buyer_id)
            .options(selectinload(Review.buyer))
            .order_by(Review.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def create(self, review: Review) -> Review:
        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)
        return review
