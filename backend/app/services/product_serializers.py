from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from app.schemas.product import ProductDetail, ProductImageOut, ProductListItem, SellerBrief

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.user import User


def seller_is_hot(rating_avg: object, hot_threshold: float = 4.5) -> bool:
    if rating_avg is None:
        return False
    return float(rating_avg) >= hot_threshold


def serialize_seller(user: "User") -> SellerBrief:
    ra = user.rating_avg
    rv = float(ra) if ra is not None else None
    return SellerBrief(
        id=user.id,
        nickname=user.nickname,
        avatar_url=user.avatar_url,
        rating_avg=rv,
    )


def cover_image_path(product: "Product") -> Optional[str]:
    images = list(product.images)
    if not images:
        return None
    images.sort(key=lambda i: i.sort_order)
    return images[0].path


def serialize_product_list_item(product: "Product", hot_threshold: float = 4.5) -> ProductListItem:
    seller = serialize_seller(product.seller)
    return ProductListItem(
        id=product.id,
        title=product.title,
        price=float(product.price),
        condition=product.condition,
        trade_type=product.trade_type,
        stock=product.stock,
        category_id=product.category_id,
        category_name=product.category.name,
        cover_image=cover_image_path(product),
        is_hot=seller_is_hot(product.seller.rating_avg, hot_threshold),
        seller=seller,
        created_at=product.created_at,
    )


def serialize_product_detail(
    product: "Product",
    viewer: Optional["User"],
    hot_threshold: float = 4.5,
) -> ProductDetail:
    reject_reason: Optional[str] = None
    if product.status == "rejected" and viewer is not None:
        if viewer.role == "admin" or viewer.id == product.seller_id:
            reject_reason = product.reject_reason

    imgs = [ProductImageOut.model_validate(i) for i in sorted(product.images, key=lambda x: x.sort_order)]
    seller = serialize_seller(product.seller)
    return ProductDetail(
        id=product.id,
        title=product.title,
        description=product.description,
        price=float(product.price),
        condition=product.condition,
        trade_type=product.trade_type,
        stock=product.stock,
        status=product.status,
        reject_reason=reject_reason,
        category_id=product.category_id,
        category_name=product.category.name,
        images=imgs,
        is_hot=seller_is_hot(product.seller.rating_avg, hot_threshold),
        seller=seller,
        created_at=product.created_at,
        updated_at=product.updated_at,
    )


def touch_product_updated(product: "Product") -> None:
    product.updated_at = datetime.now(timezone.utc)
