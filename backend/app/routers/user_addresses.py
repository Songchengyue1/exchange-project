from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.user_address import UserAddress
from app.repositories.user_address import UserAddressRepository
from app.schemas.user_address import UserAddressCreate, UserAddressPublic, UserAddressUpdate
from app.services.address_format import format_address

router = APIRouter(prefix="/users/me/addresses", tags=["addresses"])


def _to_public(addr: UserAddress) -> UserAddressPublic:
    return UserAddressPublic(
        id=addr.id,
        label=addr.label,
        contact_name=addr.contact_name,
        phone=addr.phone,
        province=addr.province,
        city=addr.city,
        district=addr.district,
        detail=addr.detail,
        poi_name=addr.poi_name,
        latitude=addr.latitude,
        longitude=addr.longitude,
        is_default=addr.is_default,
        formatted=format_address(addr),
        created_at=addr.created_at,
        updated_at=addr.updated_at,
    )


@router.get("", response_model=list[UserAddressPublic])
def list_my_addresses(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[UserAddressPublic]:
    repo = UserAddressRepository(db)
    rows = repo.ensure_legacy_migrated(user)
    return [_to_public(a) for a in rows]


@router.post("", response_model=UserAddressPublic, status_code=status.HTTP_201_CREATED)
def create_address(
    payload: UserAddressCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> UserAddressPublic:
    repo = UserAddressRepository(db)
    if repo.count_for_user(user.id) >= 10:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="最多保存 10 个地址")
    addr = UserAddress(
        user_id=user.id,
        label=payload.label.strip() or "默认",
        contact_name=payload.contact_name.strip(),
        phone=payload.phone.strip(),
        province=payload.province.strip() if payload.province else None,
        city=payload.city.strip() if payload.city else None,
        district=payload.district.strip() if payload.district else None,
        detail=payload.detail.strip(),
        poi_name=payload.poi_name.strip() if payload.poi_name else None,
        latitude=payload.latitude,
        longitude=payload.longitude,
        is_default=payload.is_default,
    )
    addr = repo.create(addr, make_default=payload.is_default)
    return _to_public(addr)


@router.patch("/{address_id}", response_model=UserAddressPublic)
def update_address(
    address_id: int,
    payload: UserAddressUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> UserAddressPublic:
    repo = UserAddressRepository(db)
    addr = repo.get_for_user(address_id, user.id)
    if addr is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="地址不存在")
    data = payload.model_dump(exclude_unset=True)
    want_default = data.pop("is_default", None)
    for key, value in data.items():
        if isinstance(value, str):
            stripped = value.strip()
            if key in ("province", "city", "district", "poi_name") and not stripped:
                value = None
            elif key in ("contact_name", "phone", "detail", "label"):
                value = stripped
            else:
                value = stripped or value
        setattr(addr, key, value)
    addr = repo.save(addr)
    if want_default:
        addr = repo.set_default(addr)
    return _to_public(addr)


@router.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_address(
    address_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    repo = UserAddressRepository(db)
    addr = repo.get_for_user(address_id, user.id)
    if addr is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="地址不存在")
    repo.delete(addr)


@router.post("/{address_id}/default", response_model=UserAddressPublic)
def set_default_address(
    address_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> UserAddressPublic:
    repo = UserAddressRepository(db)
    addr = repo.get_for_user(address_id, user.id)
    if addr is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="地址不存在")
    addr = repo.set_default(addr)
    return _to_public(addr)
