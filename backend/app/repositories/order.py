from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.order import Order
from app.models.product import Product

_ORDER_LOAD = (
    selectinload(Order.buyer),
    selectinload(Order.seller),
    selectinload(Order.product).selectinload(Product.images),
)


class OrderRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, order_id: int) -> Optional[Order]:
        return self.db.get(Order, order_id)

    def get_detail(self, order_id: int) -> Optional[Order]:
        stmt = select(Order).where(Order.id == order_id).options(*_ORDER_LOAD)
        return self.db.scalars(stmt).first()

    def list_by_buyer(self, buyer_id: int, status_filter: Optional[str] = None) -> list[Order]:
        stmt = select(Order).where(Order.buyer_id == buyer_id).options(*_ORDER_LOAD)
        if status_filter:
            stmt = stmt.where(Order.status == status_filter)
        stmt = stmt.order_by(Order.created_at.desc())
        return list(self.db.scalars(stmt).all())

    def list_by_seller(self, seller_id: int, status_filter: Optional[str] = None) -> list[Order]:
        stmt = select(Order).where(Order.seller_id == seller_id).options(*_ORDER_LOAD)
        if status_filter:
            stmt = stmt.where(Order.status == status_filter)
        stmt = stmt.order_by(Order.created_at.desc())
        return list(self.db.scalars(stmt).all())

    def create(self, order: Order) -> Order:
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        return order

    def create_with_product(self, order: Order, product: Product) -> Order:
        self.db.add(product)
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        return order

    def save_with_product(self, order: Order, product: Product | None = None) -> Order:
        if product is not None:
            self.db.add(product)
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        return order

    def save(self, order: Order) -> Order:
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        return order

    def list_all(self, status_filter: Optional[str] = None, limit: int = 100) -> list[Order]:
        stmt = select(Order).options(*_ORDER_LOAD)
        if status_filter:
            stmt = stmt.where(Order.status == status_filter)
        stmt = stmt.order_by(Order.created_at.desc()).limit(limit)
        return list(self.db.scalars(stmt).all())
