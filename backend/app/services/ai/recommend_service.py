from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.product import Product
from app.repositories.browse_history import BrowseHistoryRepository
from app.repositories.settings import SettingsRepository
from app.schemas.ai import AIRecommendOut
from app.services.ai.embedding_index import EmbeddingIndexService
from app.services.ai.ollama_client import OllamaClient
from app.services.ai.vector_math import average_vectors
from app.services.product_serializers import serialize_product_list_item


class AIRecommendService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.history = BrowseHistoryRepository(db)
        self.embeddings = EmbeddingIndexService(db)
        self.client = OllamaClient()

    def recommend(self, user_id: Optional[int], *, limit: int = 8) -> AIRecommendOut:
        hot = SettingsRepository(self.db).hot_rating_threshold()

        if user_id is not None:
            recent_ids = self.history.recent_product_ids(user_id, limit=5)
            if recent_ids and self.client.is_available():
                vectors = []
                exclude = set(recent_ids)
                from app.repositories.product import ProductRepository

                products_repo = ProductRepository(self.db)
                for pid in recent_ids:
                    p = products_repo.get_detail(pid)
                    if p is None or p.status != "approved":
                        continue
                    vec = self.embeddings.ensure_product_embedding(p)
                    if vec:
                        vectors.append(vec)
                avg = average_vectors(vectors)
                if avg:
                    similar = self.embeddings.similarity_search(avg, top_k=limit + len(exclude), exclude_ids=exclude)
                    product_ids = [pid for pid, _ in similar[:limit]]
                    products = self._load_products(product_ids)
                    if products:
                        items = [serialize_product_list_item(p, hot_threshold=hot) for p in products]
                        return AIRecommendOut(items=items, mode="history_vector")

        popular = self._popular_products(limit)
        if popular:
            items = [serialize_product_list_item(p, hot_threshold=hot) for p in popular]
            return AIRecommendOut(items=items, mode="popular")
        return AIRecommendOut(items=[], mode="empty")

    def _load_products(self, ids: list[int]) -> list[Product]:
        if not ids:
            return []
        stmt = (
            select(Product)
            .where(Product.id.in_(ids), Product.status == "approved")
            .options(
                selectinload(Product.images),
                selectinload(Product.seller),
                selectinload(Product.category),
            )
        )
        rows = {p.id: p for p in self.db.scalars(stmt).all()}
        return [rows[i] for i in ids if i in rows]

    def _popular_products(self, limit: int) -> list[Product]:
        from sqlalchemy import desc

        from app.models.user import User

        stmt = (
            select(Product)
            .join(User, User.id == Product.seller_id)
            .where(Product.status == "approved")
            .options(
                selectinload(Product.images),
                selectinload(Product.seller),
                selectinload(Product.category),
            )
            .order_by(desc(User.rating_avg).nullslast(), Product.created_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())
