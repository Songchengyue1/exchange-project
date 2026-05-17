from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    sort_order: int = 0


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=64)
    sort_order: Optional[int] = None


class CategoryPublic(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    sort_order: int
