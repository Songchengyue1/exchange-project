from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AdminUserItem(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    username: str
    nickname: str
    role: str
    is_disabled: bool
    phone: Optional[str] = None
    rating_avg: Optional[float] = None
    created_at: datetime


class AdminUserPatch(BaseModel):
    is_disabled: bool


class AdminResetPasswordBody(BaseModel):
    new_password: str = Field(min_length=6, max_length=128)


class AdminOrderItem(BaseModel):
    id: int
    product_id: int
    product_title: str
    amount: float
    quantity: int
    status: str
    trade_type: str
    refund_reason: Optional[str] = None
    refund_reject_reason: Optional[str] = None
    buyer_id: int
    buyer_nickname: str
    seller_id: int
    seller_nickname: str
    created_at: datetime
    updated_at: datetime


class AdminRefundRejectBody(BaseModel):
    note: Optional[str] = Field(None, max_length=500)


class AdminAuditLogItem(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    admin_id: int
    admin_username: str
    action: str
    target_type: str
    target_id: int
    detail: Optional[str] = None
    created_at: datetime
