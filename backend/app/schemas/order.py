from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.schemas.review import ReviewPublic

OrderStatus = Literal[
    "pending_payment",
    "pending_fulfillment",
    "completed",
    "cancelled",
    "refund_pending",
    "refunded",
]


class RefundRequestBody(BaseModel):
    reason: str = Field(min_length=1, max_length=500)


class OrderCreate(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1, le=99)
    remark: Optional[str] = Field(None, max_length=500)
    shipping_address_id: Optional[int] = None


class MockPayBody(BaseModel):
    success: bool = True


class OrderUserBrief(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    nickname: str
    avatar_url: Optional[str] = None


class OrderProductBrief(BaseModel):
    id: int
    title: str
    cover_image: Optional[str] = None
    trade_type: str


class OrderDetail(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: float
    amount: float
    product_title: str
    trade_type: str
    status: str
    remark: Optional[str] = None
    shipping_address_snapshot: Optional[str] = None
    payment_ref: Optional[str] = None
    buyer: OrderUserBrief
    seller: OrderUserBrief
    product: OrderProductBrief
    created_at: datetime
    updated_at: datetime
    paid_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    refund_reason: Optional[str] = None
    buyer_has_reviewed: bool = False
    review: Optional[ReviewPublic] = None
    payment_expires_at: Optional[datetime] = None


class OrderListItem(BaseModel):
    id: int
    product_id: int
    product_title: str
    amount: float
    quantity: int
    trade_type: str
    status: str
    cover_image: Optional[str] = None
    counterparty_nickname: str
    created_at: datetime
    payment_expires_at: Optional[datetime] = None
