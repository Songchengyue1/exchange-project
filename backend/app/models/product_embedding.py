from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ProductEmbedding(Base):
    __tablename__ = "product_embeddings"

    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), primary_key=True)
    model: Mapped[str] = mapped_column(String(64))
    embedding_json: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
