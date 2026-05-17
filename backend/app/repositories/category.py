from __future__ import annotations

from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.product import Product


class CategoryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_all(self) -> list[Category]:
        return list(
            self.db.scalars(
                select(Category).order_by(Category.sort_order.asc(), Category.id.asc())
            ).all()
        )

    def get_by_id(self, category_id: int) -> Optional[Category]:
        return self.db.get(Category, category_id)

    def create(self, category: Category) -> Category:
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def save(self, category: Category) -> Category:
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def delete(self, category: Category) -> None:
        self.db.delete(category)
        self.db.commit()

    def count_products(self, category_id: int) -> int:
        return int(
            self.db.scalar(select(func.count(Product.id)).where(Product.category_id == category_id))
            or 0
        )

    def name_exists(self, name: str, exclude_id: Optional[int] = None) -> bool:
        stmt = select(Category.id).where(Category.name == name)
        if exclude_id is not None:
            stmt = stmt.where(Category.id != exclude_id)
        return self.db.scalar(stmt) is not None
