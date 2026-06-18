from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.schemas.product import ProductListItem


class BrowseRecordIn(BaseModel):
    product_id: int


class AISearchIn(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    page: int = 1
    page_size: int = 12


class AISearchOut(BaseModel):
    items: list[ProductListItem]
    total: int
    page: int
    page_size: int
    mode: Literal["hybrid", "keyword", "vector"]
    used_llm: bool = False
    fallback: bool = False


class AISearchByImageOut(AISearchOut):
    """识图搜索结果：在普通搜索结果上附带识别信息。"""

    recognized_item: Optional[str] = None
    keywords: list[str] = Field(default_factory=list)
    query: str = ""


class AIRecommendOut(BaseModel):
    items: list[ProductListItem]
    mode: Literal["history_vector", "popular", "empty"]


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    conversation_id: Optional[int] = None


class AIProductRef(BaseModel):
    id: int
    title: str


class AIMessageOut(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime
    product_ids: list[int] = Field(default_factory=list)
    product_refs: list[AIProductRef] = Field(default_factory=list)
    products_kind: Optional[Literal["target", "recommend"]] = None

    model_config = {"from_attributes": True}


class AIConversationOut(BaseModel):
    id: int
    title: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AIConversationDetail(AIConversationOut):
    messages: list[AIMessageOut]
