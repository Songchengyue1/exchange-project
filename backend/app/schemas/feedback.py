from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

FeedbackStatus = Literal["pending", "processing", "resolved"]


class FeedbackCreate(BaseModel):
    subject: str = Field(min_length=1, max_length=120)
    content: str = Field(min_length=1, max_length=5000)


class FeedbackPublic(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    subject: str
    content: str
    status: str
    admin_reply: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class FeedbackAdminItem(FeedbackPublic):
    user_id: int
    username: str
    nickname: str


class FeedbackAdminUpdate(BaseModel):
    status: FeedbackStatus
    admin_reply: Optional[str] = Field(None, max_length=2000)
