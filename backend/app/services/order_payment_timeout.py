from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.order import Order
from app.repositories import OrderRepository, ProductRepository
from app.services.product_serializers import touch_product_updated

PAYMENT_TIMEOUT_MINUTES = 30


def payment_expires_at(created_at: datetime) -> datetime:
    base = created_at
    if base.tzinfo is None:
        base = base.replace(tzinfo=timezone.utc)
    return base + timedelta(minutes=PAYMENT_TIMEOUT_MINUTES)


def is_payment_expired(created_at: datetime, *, now: datetime | None = None) -> bool:
    now = now or datetime.now(timezone.utc)
    return now >= payment_expires_at(created_at)


def cancel_pending_payment_order(db: Session, order: Order) -> bool:
    """取消待付款订单并恢复库存。若订单非待付款则返回 False。"""
    if order.status != "pending_payment":
        return False

    product = ProductRepository(db).get_by_id(order.product_id)
    if product is not None:
        product.stock += order.quantity
        touch_product_updated(product)

    order.status = "cancelled"
    order.updated_at = datetime.now(timezone.utc)
    OrderRepository(db).save_with_product(order, product)
    return True


def expire_pending_payment_if_needed(db: Session, order: Order) -> bool:
    """若待付款已超时则自动取消，返回是否已取消。"""
    if order.status != "pending_payment":
        return False
    if not is_payment_expired(order.created_at):
        return False
    return cancel_pending_payment_order(db, order)
