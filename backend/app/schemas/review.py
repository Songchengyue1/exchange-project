from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=2000)


class ReviewPublic(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    order_id: int
    product_id: int
    rating: int
    comment: Optional[str] = None
    buyer_nickname: str
    created_at: datetime
