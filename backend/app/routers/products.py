from __future__ import annotations

import uuid
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, get_optional_user
from app.models.product import Product
from app.models.product_favorite import ProductFavorite
from app.models.product_image import ProductImage
from app.models.user import User
from app.repositories import CategoryRepository, ProductRepository, SettingsRepository
from app.repositories.product import SORT_MAP
from app.schemas.product import (
    ProductCreate,
    ProductDetail,
    ProductFavoriteItem,
    ProductFavoriteState,
    ProductPage,
    ProductUpdate,
)
from app.services.product_serializers import (
    serialize_product_detail,
    serialize_product_list_item,
    touch_product_updated,
)

router = APIRouter(prefix="/products", tags=["products"])

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
EXT_BY_TYPE = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
MAX_IMAGE_BYTES = 2 * 1024 * 1024
MAX_IMAGES_PER_PRODUCT = 6

# 修改这些字段后需重新审核；仅改 stock 不打回 pending
_REVIEW_TRIGGER_FIELDS = frozenset(
    {"category_id", "title", "description", "price", "condition", "trade_type"}
)


def _assert_visible(product: Product, viewer: Optional[User]) -> None:
    if product.status == "approved":
        return
    if viewer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="商品不存在")
    if viewer.role == "admin" or viewer.id == product.seller_id:
        return
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="商品不存在")


@router.get("/mine", response_model=list[ProductDetail])
def list_my_products(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ProductDetail]:
    hot = SettingsRepository(db).hot_rating_threshold()
    products = ProductRepository(db)
    rows = products.list_by_seller(user.id, status_filter)
    return [serialize_product_detail(p, viewer=user, hot_threshold=hot) for p in rows]


@router.get("", response_model=ProductPage)
def list_marketplace_products(
    page: int = 1,
    page_size: int = 12,
    category_id: Optional[int] = None,
    q: Optional[str] = None,
    sort: str = "created_at_desc",
    db: Session = Depends(get_db),
) -> ProductPage:
    if page < 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="page 无效")
    if page_size < 1 or page_size > 50:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="page_size 无效")
    if sort not in SORT_MAP:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="sort 无效")

    hot = SettingsRepository(db).hot_rating_threshold()
    rows, total = ProductRepository(db).list_marketplace(
        page=page,
        page_size=page_size,
        category_id=category_id,
        q=q,
        sort=sort,
    )
    items = [serialize_product_list_item(p, hot_threshold=hot) for p in rows]
    return ProductPage(items=items, total=total, page=page, page_size=page_size)


def _favorite_count(db: Session, product_id: int) -> int:
    return int(
        db.scalar(select(func.count(ProductFavorite.id)).where(ProductFavorite.product_id == product_id)) or 0
    )


def _favorite_state(db: Session, product_id: int, is_favorited: bool) -> ProductFavoriteState:
    return ProductFavoriteState(
        product_id=product_id,
        is_favorited=is_favorited,
        favorite_count=_favorite_count(db, product_id),
    )


@router.get("/favorites", response_model=list[ProductFavoriteItem])
def list_favorite_products(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ProductFavoriteItem]:
    hot = SettingsRepository(db).hot_rating_threshold()
    rows = ProductRepository(db).list_favorites(user.id)
    return [
        ProductFavoriteItem(
            product=serialize_product_list_item(p, hot_threshold=hot, viewer=user),
            created_at=created_at,
        )
        for p, created_at in rows
    ]


@router.post("", response_model=ProductDetail, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProductDetail:
    if CategoryRepository(db).get_by_id(payload.category_id) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="分类不存在")
    product = Product(
        seller_id=user.id,
        category_id=payload.category_id,
        title=payload.title.strip(),
        description=(payload.description or "").strip(),
        price=payload.price,
        condition=payload.condition,
        trade_type=payload.trade_type,
        stock=payload.stock,
        status="pending",
        reject_reason=None,
    )
    products = ProductRepository(db)
    products.create(product)
    loaded = products.get_detail(product.id)
    assert loaded is not None
    hot = SettingsRepository(db).hot_rating_threshold()
    return serialize_product_detail(loaded, viewer=user, hot_threshold=hot)


@router.get("/{product_id}", response_model=ProductDetail)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    viewer: Optional[User] = Depends(get_optional_user),
) -> ProductDetail:
    product = ProductRepository(db).get_detail(product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="商品不存在")
    _assert_visible(product, viewer)
    hot = SettingsRepository(db).hot_rating_threshold()
    return serialize_product_detail(product, viewer=viewer, hot_threshold=hot)


@router.post("/{product_id}/favorite", response_model=ProductFavoriteState)
def favorite_product(
    product_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProductFavoriteState:
    product = ProductRepository(db).get_by_id(product_id)
    if product is None or product.status != "approved":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="商品不存在")
    if product.seller_id == user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="不能收藏自己的商品")

    existing = db.scalar(
        select(ProductFavorite).where(
            ProductFavorite.user_id == user.id,
            ProductFavorite.product_id == product_id,
        )
    )
    if existing is None:
        db.add(ProductFavorite(user_id=user.id, product_id=product_id))
        db.commit()
    return _favorite_state(db, product_id, True)


@router.delete("/{product_id}/favorite", response_model=ProductFavoriteState)
def unfavorite_product(
    product_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProductFavoriteState:
    fav = db.scalar(
        select(ProductFavorite).where(
            ProductFavorite.user_id == user.id,
            ProductFavorite.product_id == product_id,
        )
    )
    if fav is not None:
        db.delete(fav)
        db.commit()
    return _favorite_state(db, product_id, False)


@router.patch("/{product_id}", response_model=ProductDetail)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProductDetail:
    products = ProductRepository(db)
    product = products.get_by_id(product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="商品不存在")
    if product.seller_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权修改该商品")
    if product.status not in ("pending", "approved", "rejected", "offline"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="当前状态不可编辑")

    data = payload.model_dump(exclude_unset=True)
    if "category_id" in data and data["category_id"] is not None:
        if CategoryRepository(db).get_by_id(data["category_id"]) is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="分类不存在")
    if "title" in data and data["title"] is not None:
        data["title"] = data["title"].strip()
    if "description" in data and data["description"] is not None:
        data["description"] = data["description"].strip()

    for k, v in data.items():
        setattr(product, k, v)

    if data.keys() & _REVIEW_TRIGGER_FIELDS and product.status in ("approved", "rejected", "offline"):
        product.status = "pending"
        product.reject_reason = None

    touch_product_updated(product)
    products.save(product)
    loaded = products.get_detail(product_id)
    assert loaded is not None
    hot = SettingsRepository(db).hot_rating_threshold()
    return serialize_product_detail(loaded, viewer=user, hot_threshold=hot)


@router.post("/{product_id}/offline", response_model=ProductDetail)
def offline_product(
    product_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProductDetail:
    products = ProductRepository(db)
    product = products.get_by_id(product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="商品不存在")
    if product.seller_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作该商品")
    if product.status == "offline":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="已下架")
    product.status = "offline"
    touch_product_updated(product)
    products.save(product)
    loaded = products.get_detail(product_id)
    assert loaded is not None
    hot = SettingsRepository(db).hot_rating_threshold()
    return serialize_product_detail(loaded, viewer=user, hot_threshold=hot)


@router.post("/{product_id}/images", response_model=ProductDetail)
async def upload_product_images(
    product_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ProductDetail:
    if not files:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请选择图片文件")
    products = ProductRepository(db)
    product = products.get_detail(product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="商品不存在")
    if product.seller_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权操作该商品")
    if product.status not in ("pending", "approved", "rejected", "offline"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="当前状态不可上传图片")

    existing = len(product.images)
    if existing + len(files) > MAX_IMAGES_PER_PRODUCT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"每个商品最多 {MAX_IMAGES_PER_PRODUCT} 张图片",
        )

    upload_dir = Path("uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)

    next_order = max((i.sort_order for i in product.images), default=-1) + 1

    for file in files:
        if file.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="仅支持 JPG / PNG / WEBP")
        body = await file.read()
        if len(body) > MAX_IMAGE_BYTES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="单张图片不能超过 2MB")
        ext = EXT_BY_TYPE[file.content_type]
        name = f"p{product_id}_{uuid.uuid4().hex}{ext}"
        (upload_dir / name).write_bytes(body)
        products.add_image(
            ProductImage(product_id=product.id, path=f"/static/{name}", sort_order=next_order)
        )
        next_order += 1

    if product.status in ("approved", "rejected", "offline"):
        product.status = "pending"
        product.reject_reason = None

    touch_product_updated(product)
    products.commit()
    loaded = products.get_detail(product_id)
    assert loaded is not None
    hot = SettingsRepository(db).hot_rating_threshold()
    return serialize_product_detail(loaded, viewer=user, hot_threshold=hot)
