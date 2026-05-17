from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.ai_conversation import AIConversation
    from app.models.product import Product
    from app.models.user_address import UserAddress


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(16), default="user")
    nickname: Mapped[str] = mapped_column(String(64))
    phone: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    is_disabled: Mapped[bool] = mapped_column(Boolean, default=False)
    rating_avg: Mapped[Optional[float]] = mapped_column(Numeric(4, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    products: Mapped[list["Product"]] = relationship("Product", back_populates="seller")
    ai_conversations: Mapped[list["AIConversation"]] = relationship(
        "AIConversation",
        back_populates="user",
    )
    addresses: Mapped[list["UserAddress"]] = relationship(
        "UserAddress",
        back_populates="user",
        cascade="all, delete-orphan",
    )
