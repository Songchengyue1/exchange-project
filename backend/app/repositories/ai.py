from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.ai_conversation import AIConversation
from app.models.ai_message import AIMessage


class AIConversationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, conversation_id: int, user_id: int) -> Optional[AIConversation]:
        stmt = (
            select(AIConversation)
            .where(AIConversation.id == conversation_id, AIConversation.user_id == user_id)
            .options(selectinload(AIConversation.messages))
        )
        return self.db.scalars(stmt).first()

    def list_for_user(self, user_id: int, limit: int = 20) -> list[AIConversation]:
        stmt = (
            select(AIConversation)
            .where(AIConversation.user_id == user_id)
            .order_by(AIConversation.updated_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def create(self, user_id: int, title: Optional[str] = None) -> AIConversation:
        conv = AIConversation(user_id=user_id, title=title)
        self.db.add(conv)
        self.db.commit()
        self.db.refresh(conv)
        return conv

    def touch(self, conv: AIConversation) -> None:
        conv.updated_at = datetime.now(timezone.utc)
        self.db.add(conv)
        self.db.commit()

    def add_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
        meta_json: Optional[str] = None,
    ) -> AIMessage:
        msg = AIMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            meta_json=meta_json,
        )
        self.db.add(msg)
        self.db.commit()
        self.db.refresh(msg)
        return msg

    def delete(self, conversation_id: int, user_id: int) -> bool:
        conv = self.get(conversation_id, user_id)
        if conv is None:
            return False
        self.db.delete(conv)
        self.db.commit()
        return True

    def recent_messages(self, conversation_id: int, limit: int = 10) -> list[AIMessage]:
        stmt = (
            select(AIMessage)
            .where(AIMessage.conversation_id == conversation_id)
            .order_by(AIMessage.created_at.desc())
            .limit(limit)
        )
        rows = list(self.db.scalars(stmt).all())
        rows.reverse()
        return rows
