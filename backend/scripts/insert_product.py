#!/usr/bin/env python3
"""录入单条商品到 PostgreSQL（开发/演示用）。

示例：
  cd backend
  .venv/bin/python scripts/insert_product.py \\
    --seller demo_seller1 --category 数码 \\
    --title "测试商品" --price 99 --condition excellent \\
    --trade-type both --description "说明" \\
    --image seed_images/demo_p1_iphone.png --status approved
"""
from __future__ import annotations

import argparse
import shutil
import sys
import uuid
from decimal import Decimal
from pathlib import Path

# 保证可从 backend 根目录导入 app
_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from sqlalchemy import select

from app.database import SessionLocal
from app.models.category import Category
from app.models.product import Product
from app.models.product_image import ProductImage
from app.models.user import User

VALID_CONDITIONS = {"brand_new", "like_new", "excellent", "good", "fair"}
VALID_TRADE = {"pickup", "shipping", "both"}
VALID_STATUS = {"pending", "approved", "rejected", "offline"}
CATEGORY_BY_NAME = {"数码": 1, "服饰": 2, "图书": 3, "家居": 4, "其他": 5}
UPLOADS = _BACKEND / "uploads"
MAX_IMAGES = 6


def _resolve_category_id(db, raw: str) -> int:
    if raw.isdigit():
        cid = int(raw)
        if db.get(Category, cid):
            return cid
        raise SystemExit(f"分类 id 不存在: {cid}")
    if raw in CATEGORY_BY_NAME:
        return CATEGORY_BY_NAME[raw]
    row = db.scalar(select(Category.id).where(Category.name == raw))
    if row is None:
        raise SystemExit(f"未知分类: {raw}")
    return row


def _resolve_seller_id(db, username: str | None, seller_id: int | None) -> int:
    if seller_id is not None:
        if db.get(User, seller_id) is None:
            raise SystemExit(f"用户 id 不存在: {seller_id}")
        return seller_id
    if not username:
        raise SystemExit("请指定 --seller 或 --seller-id")
    user = db.scalar(select(User).where(User.username == username))
    if user is None:
        raise SystemExit(f"用户不存在: {username}")
    return user.id


def main() -> None:
    p = argparse.ArgumentParser(description="录入商品到数据库")
    p.add_argument("--seller", help="卖家用户名")
    p.add_argument("--seller-id", type=int, help="卖家 user id")
    p.add_argument("--category", required=True, help="分类名或 id")
    p.add_argument("--title", required=True)
    p.add_argument("--price", type=Decimal, required=True)
    p.add_argument("--condition", required=True, choices=sorted(VALID_CONDITIONS))
    p.add_argument("--trade-type", required=True, choices=sorted(VALID_TRADE))
    p.add_argument("--stock", type=int, default=1)
    p.add_argument("--description", default="")
    p.add_argument("--status", default="pending", choices=sorted(VALID_STATUS))
    p.add_argument("--image", action="append", default=[], help="图片路径，可多次指定")
    args = p.parse_args()

    if args.price <= 0:
        raise SystemExit("价格须大于 0")
    if args.stock < 1:
        raise SystemExit("库存须 >= 1")
    if len(args.image) > MAX_IMAGES:
        raise SystemExit(f"最多 {MAX_IMAGES} 张图片")

    UPLOADS.mkdir(parents=True, exist_ok=True)

    with SessionLocal() as db:
        seller_id = _resolve_seller_id(db, args.seller, args.seller_id)
        category_id = _resolve_category_id(db, args.category)

        product = Product(
            seller_id=seller_id,
            category_id=category_id,
            title=args.title.strip(),
            description=(args.description or "").strip(),
            price=args.price,
            condition=args.condition,
            trade_type=args.trade_type,
            stock=args.stock,
            status=args.status,
            reject_reason=None,
        )
        db.add(product)
        db.flush()

        for i, img_path in enumerate(args.image):
            src = Path(img_path)
            if not src.is_file():
                raise SystemExit(f"图片不存在: {src}")
            ext = src.suffix.lower()
            if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
                raise SystemExit(f"不支持的图片格式: {ext}")
            name = f"p{product.id}_{uuid.uuid4().hex}{ext}"
            shutil.copy2(src, UPLOADS / name)
            db.add(
                ProductImage(
                    product_id=product.id,
                    path=f"/static/{name}",
                    sort_order=i,
                )
            )

        db.commit()
        db.refresh(product)
        print(f"OK product_id={product.id} status={product.status} images={len(args.image)}")


if __name__ == "__main__":
    main()
