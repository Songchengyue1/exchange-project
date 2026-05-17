from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, Field

ConditionCode = Literal["brand_new", "like_new", "excellent", "good", "fair"]
TradeType = Literal["pickup", "shipping", "both"]


class ProductImageOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    path: str
    sort_order: int


class SellerBrief(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    nickname: str
    avatar_url: Optional[str] = None
    rating_avg: Optional[float] = None


class ProductCreate(BaseModel):
    category_id: int
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=20000)
    price: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    condition: ConditionCode
    trade_type: TradeType
    stock: int = Field(default=1, ge=1, le=99999)


class ProductUpdate(BaseModel):
    category_id: Optional[int] = None
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=20000)
    price: Optional[Decimal] = Field(None, gt=0, max_digits=12, decimal_places=2)
    condition: Optional[ConditionCode] = None
    trade_type: Optional[TradeType] = None
    stock: Optional[int] = Field(None, ge=0, le=99999)


class ProductListItem(BaseModel):
    id: int
    title: str
    price: float
    condition: str
    trade_type: str
    stock: int
    category_id: int
    category_name: str
    cover_image: Optional[str] = None
    is_hot: bool
    seller: SellerBrief
    created_at: datetime


class ProductDetail(BaseModel):
    id: int
    title: str
    description: str
    price: float
    condition: str
    trade_type: str
    stock: int
    status: str
    reject_reason: Optional[str] = None
    category_id: int
    category_name: str
    images: list[ProductImageOut]
    is_hot: bool
    seller: SellerBrief
    created_at: datetime
    updated_at: datetime


class ProductPage(BaseModel):
    items: list[ProductListItem]
    total: int
    page: int
    page_size: int


class RejectBody(BaseModel):
    reason: str = Field(min_length=1, max_length=500)
