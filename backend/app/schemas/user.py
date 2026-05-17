from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=32, pattern=r"^[a-zA-Z0-9_]+$")
    password: str = Field(min_length=6, max_length=128)


class UserLogin(BaseModel):
    username: str
    password: str


class UserPublic(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    username: str
    nickname: str
    phone: Optional[str] = None
    address: Optional[str] = None
    avatar_url: Optional[str] = None
    role: str
    rating_avg: Optional[float] = None
    created_at: datetime


class UserUpdate(BaseModel):
    nickname: Optional[str] = Field(None, min_length=1, max_length=64)
    phone: Optional[str] = Field(None, max_length=32)
    address: Optional[str] = Field(None, max_length=2000)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserPublic
