from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.feedback import Feedback


class FeedbackRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, feedback_id: int) -> Optional[Feedback]:
        stmt = (
            select(Feedback)
            .where(Feedback.id == feedback_id)
            .options(selectinload(Feedback.user))
        )
        return self.db.scalars(stmt).first()

    def list_by_user(self, user_id: int) -> list[Feedback]:
        stmt = (
            select(Feedback)
            .where(Feedback.user_id == user_id)
            .order_by(Feedback.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def list_all(self, status_filter: Optional[str] = None) -> list[Feedback]:
        stmt = select(Feedback).options(selectinload(Feedback.user)).order_by(Feedback.created_at.desc())
        if status_filter:
            stmt = stmt.where(Feedback.status == status_filter)
        return list(self.db.scalars(stmt).all())

    def create(self, feedback: Feedback) -> Feedback:
        self.db.add(feedback)
        self.db.commit()
        self.db.refresh(feedback)
        return feedback

    def save(self, feedback: Feedback) -> Feedback:
        self.db.add(feedback)
        self.db.commit()
        self.db.refresh(feedback)
        return feedback
