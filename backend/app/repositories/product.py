from __future__ import annotations

from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.product import Product
from app.models.product_favorite import ProductFavorite
from app.models.product_image import ProductImage

_PRODUCT_LOAD = (
    selectinload(Product.images),
    selectinload(Product.seller),
    selectinload(Product.category),
    selectinload(Product.favorites),
)

SORT_MAP = {
    "created_at_desc": (Product.created_at.desc(),),
    "price_asc": (Product.price.asc(), Product.id.desc()),
    "price_desc": (Product.price.desc(), Product.id.desc()),
}


class ProductRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, product_id: int, *, with_relations: bool = False) -> Optional[Product]:
        if with_relations:
            return self.get_detail(product_id)
        return self.db.get(Product, product_id)

    def get_detail(self, product_id: int) -> Optional[Product]:
        stmt = select(Product).where(Product.id == product_id).options(*_PRODUCT_LOAD)
        return self.db.scalars(stmt).first()

    def list_by_seller(self, seller_id: int, status_filter: Optional[str] = None) -> list[Product]:
        stmt = select(Product).where(Product.seller_id == seller_id).options(*_PRODUCT_LOAD)
        if status_filter:
            stmt = stmt.where(Product.status == status_filter)
        stmt = stmt.order_by(Product.updated_at.desc())
        return list(self.db.scalars(stmt).all())

    def list_marketplace(
        self,
        *,
        page: int,
        page_size: int,
        category_id: Optional[int] = None,
        q: Optional[str] = None,
        keywords: Optional[list[str]] = None,
        sort: str = "created_at_desc",
    ) -> tuple[list[Product], int]:
        filters = [Product.status == "approved"]
        if category_id is not None:
            filters.append(Product.category_id == category_id)
        # keywords：任一词命中标题/描述即算匹配（OR）；用于识图/智能搜索的多关键词场景
        if keywords:
            ors = []
            for kw in keywords:
                kw = kw.strip()
                if not kw:
                    continue
                term = f"%{kw}%"
                ors.append(Product.title.ilike(term))
                ors.append(Product.description.ilike(term))
            if ors:
                filters.append(or_(*ors))
        elif q and q.strip():
            term = f"%{q.strip()}%"
            filters.append(or_(Product.title.ilike(term), Product.description.ilike(term)))

        total = int(self.db.scalar(select(func.count(Product.id)).where(*filters)) or 0)
        order_by = SORT_MAP[sort]
        stmt = (
            select(Product)
            .where(*filters)
            .options(*_PRODUCT_LOAD)
            .order_by(*order_by)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self.db.scalars(stmt).all()), total

    def list_favorites(self, user_id: int) -> list[tuple[Product, object]]:
        stmt = (
            select(Product, ProductFavorite.created_at)
            .join(ProductFavorite, ProductFavorite.product_id == Product.id)
            .where(ProductFavorite.user_id == user_id)
            .options(*_PRODUCT_LOAD)
            .order_by(ProductFavorite.created_at.desc(), ProductFavorite.id.desc())
        )
        return [(row[0], row[1]) for row in self.db.execute(stmt).all()]

    def list_pending(self) -> list[Product]:
        stmt = (
            select(Product)
            .where(Product.status == "pending")
            .options(*_PRODUCT_LOAD)
            .order_by(Product.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def create(self, product: Product) -> Product:
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product

    def save(self, product: Product) -> Product:
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product

    def add_image(self, image: ProductImage) -> None:
        self.db.add(image)

    def commit(self) -> None:
        self.db.commit()
