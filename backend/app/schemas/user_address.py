from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UserAddressCreate(BaseModel):
    label: str = Field(default="默认", max_length=32)
    contact_name: str = Field(min_length=1, max_length=64)
    phone: str = Field(min_length=1, max_length=32)
    province: Optional[str] = Field(None, max_length=64)
    city: Optional[str] = Field(None, max_length=64)
    district: Optional[str] = Field(None, max_length=64)
    detail: str = Field(min_length=1, max_length=500)
    poi_name: Optional[str] = Field(None, max_length=128)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_default: bool = False


class UserAddressUpdate(BaseModel):
    label: Optional[str] = Field(None, max_length=32)
    contact_name: Optional[str] = Field(None, min_length=1, max_length=64)
    phone: Optional[str] = Field(None, min_length=1, max_length=32)
    province: Optional[str] = Field(None, max_length=64)
    city: Optional[str] = Field(None, max_length=64)
    district: Optional[str] = Field(None, max_length=64)
    detail: Optional[str] = Field(None, min_length=1, max_length=500)
    poi_name: Optional[str] = Field(None, max_length=128)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_default: Optional[bool] = None


class UserAddressPublic(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    label: str
    contact_name: str
    phone: str
    province: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    detail: str
    poi_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_default: bool
    formatted: str
    created_at: datetime
    updated_at: datetime
