from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from app.schemas.order import OrderDetail, OrderListItem, OrderProductBrief, OrderUserBrief
from app.schemas.review import ReviewPublic
from app.services.order_payment_timeout import payment_expires_at
from app.services.product_serializers import cover_image_path

if TYPE_CHECKING:
    from app.models.order import Order
    from app.models.review import Review
    from app.models.user import User


def _payment_expires_at_for(order: "Order"):
    if order.status != "pending_payment":
        return None
    return payment_expires_at(order.created_at)


def _serialize_review(review: "Review") -> ReviewPublic:
    return ReviewPublic(
        id=review.id,
        order_id=review.order_id,
        product_id=review.product_id,
        rating=review.rating,
        comment=review.comment,
        buyer_nickname=review.buyer.nickname,
        created_at=review.created_at,
    )


def serialize_order_detail(order: "Order", review: Optional["Review"] = None) -> OrderDetail:
    cover = None
    if order.product and order.product.images:
        cover = cover_image_path(order.product)
    return OrderDetail(
        id=order.id,
        product_id=order.product_id,
        quantity=order.quantity,
        unit_price=float(order.unit_price),
        amount=float(order.amount),
        product_title=order.product_title,
        trade_type=order.trade_type,
        status=order.status,
        remark=order.remark,
        shipping_address_snapshot=order.shipping_address_snapshot,
        payment_ref=order.payment_ref,
        buyer=OrderUserBrief.model_validate(order.buyer),
        seller=OrderUserBrief.model_validate(order.seller),
        product=OrderProductBrief(
            id=order.product_id,
            title=order.product_title,
            cover_image=cover,
            trade_type=order.trade_type,
        ),
        created_at=order.created_at,
        updated_at=order.updated_at,
        paid_at=order.paid_at,
        completed_at=order.completed_at,
        refund_reason=order.refund_reason,
        buyer_has_reviewed=review is not None,
        review=_serialize_review(review) if review is not None else None,
        payment_expires_at=_payment_expires_at_for(order),
    )


def serialize_order_list_item(order: "Order", viewer: "User") -> OrderListItem:
    cover = None
    if order.product and order.product.images:
        cover = cover_image_path(order.product)
    if viewer.id == order.buyer_id:
        counterparty = order.seller.nickname
    else:
        counterparty = order.buyer.nickname
    return OrderListItem(
        id=order.id,
        product_id=order.product_id,
        product_title=order.product_title,
        amount=float(order.amount),
        quantity=order.quantity,
        trade_type=order.trade_type,
        status=order.status,
        cover_image=cover,
        counterparty_nickname=counterparty,
        created_at=order.created_at,
        payment_expires_at=_payment_expires_at_for(order),
    )
