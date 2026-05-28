from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.order import Order
from app.models.review import Review
from app.models.user import User
from app.repositories import OrderRepository, ProductRepository, ReviewRepository
from app.repositories.user_address import UserAddressRepository
from app.schemas.order import MockPayBody, OrderCreate, OrderDetail, OrderListItem, RefundRequestBody
from app.schemas.review import ReviewCreate, ReviewPublic
from app.services.rating import refresh_seller_rating
from app.services.order_serializers import serialize_order_detail, serialize_order_list_item
from app.services.order_payment_timeout import (
    cancel_pending_payment_order,
    expire_pending_payment_if_needed,
    is_payment_expired,
)
from app.services.payment import get_payment_provider
from app.services.product_serializers import touch_product_updated

router = APIRouter(prefix="/orders", tags=["orders"])


def _expire_if_needed(db: Session, order: Order) -> None:
    expire_pending_payment_if_needed(db, order)


@router.get("", response_model=list[OrderListItem])
def list_buyer_orders(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[OrderListItem]:
    rows = OrderRepository(db).list_by_buyer(user.id, status_filter)
    for o in rows:
        _expire_if_needed(db, o)
    return [serialize_order_list_item(o, user) for o in rows]


def _order_detail(db: Session, order_id: int) -> OrderDetail:
    orders = OrderRepository(db)
    order = orders.get_detail(order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订单不存在")
    review = ReviewRepository(db).get_by_order_id(order_id)
    if review is not None:
        review = ReviewRepository(db).get_by_id(review.id)
    return serialize_order_detail(order, review=review)


@router.get("/sales", response_model=list[OrderListItem])
def list_seller_orders(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[OrderListItem]:
    rows = OrderRepository(db).list_by_seller(user.id, status_filter)
    for o in rows:
        _expire_if_needed(db, o)
    return [serialize_order_list_item(o, user) for o in rows]


@router.post("", response_model=OrderDetail, status_code=status.HTTP_201_CREATED)
def create_order(
    payload: OrderCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OrderDetail:
    products = ProductRepository(db)
    product = products.get_by_id(payload.product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="商品不存在")
    if product.status != "approved":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="商品未上架，无法购买")
    if product.seller_id == user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能购买自己的商品")
    if product.stock < payload.quantity:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="库存不足")

    unit_price = float(product.price)
    amount = round(unit_price * payload.quantity, 2)
    remark = payload.remark.strip() if payload.remark else None

    shipping_snapshot = None
    if payload.shipping_address_id is not None:
        addr = UserAddressRepository(db).get_for_user(payload.shipping_address_id, user.id)
        if addr is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="收货地址无效")
        shipping_snapshot = UserAddressRepository.snapshot_text(addr)
    elif product.trade_type in ("shipping", "both"):
        default_addr = next(
            (a for a in UserAddressRepository(db).ensure_legacy_migrated(user) if a.is_default),
            None,
        )
        if default_addr is None:
            rows = UserAddressRepository(db).list_for_user(user.id)
            default_addr = rows[0] if rows else None
        if default_addr is not None:
            shipping_snapshot = UserAddressRepository.snapshot_text(default_addr)

    product.stock -= payload.quantity
    touch_product_updated(product)

    order = Order(
        buyer_id=user.id,
        seller_id=product.seller_id,
        product_id=product.id,
        quantity=payload.quantity,
        unit_price=unit_price,
        amount=amount,
        product_title=product.title,
        trade_type=product.trade_type,
        status="pending_payment",
        remark=remark,
        shipping_address_snapshot=shipping_snapshot,
    )
    orders = OrderRepository(db)
    orders.create_with_product(order, product)
    loaded = orders.get_detail(order.id)
    assert loaded is not None
    return serialize_order_detail(loaded)


@router.get("/{order_id}", response_model=OrderDetail)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OrderDetail:
    order = OrderRepository(db).get_detail(order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订单不存在")
    if user.id not in (order.buyer_id, order.seller_id) and user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权查看该订单")
    _expire_if_needed(db, order)
    review_row = ReviewRepository(db).get_by_order_id(order_id)
    if review_row is not None:
        review_row = ReviewRepository(db).get_by_id(review_row.id)
    return serialize_order_detail(order, review=review_row)


@router.post("/{order_id}/mock-pay", response_model=OrderDetail)
def mock_pay_order(
    order_id: int,
    payload: MockPayBody,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OrderDetail:
    orders = OrderRepository(db)
    order = orders.get_by_id(order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订单不存在")
    if order.buyer_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅买家可支付")
    if order.status != "pending_payment":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="当前状态不可支付")
    if is_payment_expired(order.created_at):
        expire_pending_payment_if_needed(db, order)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="订单已超时，已自动取消")

    provider = get_payment_provider()
    result = provider.pay(order_id, float(order.amount), simulate_success=payload.success)
    if not result.success:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=result.message or "支付失败")

    order.status = "pending_fulfillment"
    order.payment_ref = result.payment_ref
    order.paid_at = datetime.now(timezone.utc)
    order.updated_at = datetime.now(timezone.utc)
    orders.save(order)
    loaded = orders.get_detail(order_id)
    assert loaded is not None
    return serialize_order_detail(loaded)


@router.post("/{order_id}/fulfill", response_model=OrderDetail)
def fulfill_order(
    order_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OrderDetail:
    orders = OrderRepository(db)
    order = orders.get_by_id(order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订单不存在")
    if order.seller_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅卖家可确认履约")
    if order.status != "pending_fulfillment":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="当前状态不可履约")

    now = datetime.now(timezone.utc)
    order.status = "pending_receipt"
    order.fulfilled_at = now
    order.updated_at = now
    orders.save(order)
    loaded = orders.get_detail(order_id)
    assert loaded is not None
    return serialize_order_detail(loaded)


@router.post("/{order_id}/confirm-receipt", response_model=OrderDetail)
def confirm_receipt(
    order_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OrderDetail:
    orders = OrderRepository(db)
    order = orders.get_by_id(order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订单不存在")
    if order.buyer_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅买家可确认收货")
    if order.status != "pending_receipt":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="当前状态不可确认收货")

    order.status = "completed"
    order.completed_at = datetime.now(timezone.utc)
    order.updated_at = datetime.now(timezone.utc)
    orders.save(order)
    loaded = orders.get_detail(order_id)
    assert loaded is not None
    return _order_detail(db, order_id)


@router.post("/{order_id}/review", response_model=ReviewPublic, status_code=status.HTTP_201_CREATED)
def create_order_review(
    order_id: int,
    payload: ReviewCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ReviewPublic:
    orders = OrderRepository(db)
    order = orders.get_by_id(order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订单不存在")
    if order.buyer_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅买家可评价")
    if order.status != "completed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="仅已完成订单可评价")

    reviews = ReviewRepository(db)
    if reviews.get_by_order_id(order_id) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="该订单已评价")

    comment = payload.comment.strip() if payload.comment else None
    review = Review(
        order_id=order.id,
        buyer_id=user.id,
        seller_id=order.seller_id,
        product_id=order.product_id,
        rating=payload.rating,
        comment=comment,
    )
    db.add(review)
    db.flush()
    refresh_seller_rating(db, order.seller_id)
    db.commit()
    db.refresh(review)

    loaded = reviews.get_by_id(review.id)
    assert loaded is not None
    return ReviewPublic(
        id=loaded.id,
        order_id=loaded.order_id,
        product_id=loaded.product_id,
        rating=loaded.rating,
        comment=loaded.comment,
        buyer_nickname=loaded.buyer.nickname,
        created_at=loaded.created_at,
    )


@router.post("/{order_id}/request-refund", response_model=OrderDetail)
def request_refund(
    order_id: int,
    payload: RefundRequestBody,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OrderDetail:
    orders = OrderRepository(db)
    order = orders.get_by_id(order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订单不存在")
    if order.buyer_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅买家可申请退款")
    if order.status not in ("pending_fulfillment", "pending_receipt"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="仅待卖家履约或待买家确认订单可申请退款")

    order.status = "refund_pending"
    order.refund_reason = payload.reason.strip()
    order.refund_reject_reason = None
    order.updated_at = datetime.now(timezone.utc)
    orders.save(order)
    loaded = orders.get_detail(order_id)
    assert loaded is not None
    return serialize_order_detail(loaded)


@router.post("/{order_id}/cancel", response_model=OrderDetail)
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> OrderDetail:
    orders = OrderRepository(db)
    order = orders.get_by_id(order_id)
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订单不存在")
    if order.buyer_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅买家可取消订单")
    if order.status != "pending_payment":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="仅待付款订单可取消")

    cancel_pending_payment_order(db, order)
    loaded = orders.get_detail(order_id)
    assert loaded is not None
    return serialize_order_detail(loaded)
