from __future__ import annotations

from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.user_address import UserAddress
from app.services.address_format import format_address


class UserAddressRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_for_user(self, user_id: int) -> list[UserAddress]:
        stmt = (
            select(UserAddress)
            .where(UserAddress.user_id == user_id)
            .order_by(UserAddress.is_default.desc(), UserAddress.updated_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def get_for_user(self, address_id: int, user_id: int) -> Optional[UserAddress]:
        stmt = select(UserAddress).where(
            UserAddress.id == address_id,
            UserAddress.user_id == user_id,
        )
        return self.db.scalars(stmt).first()

    def count_for_user(self, user_id: int) -> int:
        return len(self.list_for_user(user_id))

    def ensure_legacy_migrated(self, user: User) -> list[UserAddress]:
        rows = self.list_for_user(user.id)
        if rows or not (user.address and user.address.strip()):
            return rows
        phone = user.phone.strip() if user.phone else ""
        addr = UserAddress(
            user_id=user.id,
            label="默认",
            contact_name=user.nickname,
            phone=phone or "未填写",
            detail=user.address.strip(),
            is_default=True,
        )
        self.db.add(addr)
        self.db.commit()
        self.db.refresh(addr)
        return self.list_for_user(user.id)

    def _clear_default(self, user_id: int) -> None:
        self.db.execute(
            update(UserAddress).where(UserAddress.user_id == user_id).values(is_default=False)
        )

    def create(self, addr: UserAddress, make_default: bool = False) -> UserAddress:
        if make_default or not self.count_for_user(addr.user_id):
            self._clear_default(addr.user_id)
            addr.is_default = True
        self.db.add(addr)
        self.db.commit()
        self.db.refresh(addr)
        return addr

    def save(self, addr: UserAddress) -> UserAddress:
        self.db.add(addr)
        self.db.commit()
        self.db.refresh(addr)
        return addr

    def delete(self, addr: UserAddress) -> None:
        was_default = addr.is_default
        user_id = addr.user_id
        self.db.delete(addr)
        self.db.commit()
        if was_default:
            remaining = self.list_for_user(user_id)
            if remaining:
                remaining[0].is_default = True
                self.save(remaining[0])

    def set_default(self, addr: UserAddress) -> UserAddress:
        self._clear_default(addr.user_id)
        addr.is_default = True
        return self.save(addr)

    @staticmethod
    def snapshot_text(addr: UserAddress) -> str:
        contact = f"{addr.contact_name} {addr.phone}".strip()
        return f"{contact} · {format_address(addr)}"
