from __future__ import annotations

import json
import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.config import settings
from app.models.product import Product
from app.models.product_embedding import ProductEmbedding
from app.repositories.product import SORT_MAP
from app.services.ai.ollama_client import OllamaClient, OllamaError
from app.services.ai.vector_math import cosine_similarity, parse_embedding_json

logger = logging.getLogger(__name__)

# 进程内缓存商品向量，避免每次对话查库 + 解析 JSON
_embedding_cache: dict[int, list[float]] | None = None


def product_embed_text(product: Product) -> str:
    cat = product.category.name if product.category else ""
    parts = [product.title, cat, (product.description or "")[:2000]]
    return "\n".join(p for p in parts if p)


class EmbeddingIndexService:
    def __init__(self, db: Session, client: Optional[OllamaClient] = None) -> None:
        self.db = db
        self.client = client or OllamaClient()

    def get_vector(self, product_id: int) -> Optional[list[float]]:
        row = self.db.get(ProductEmbedding, product_id)
        if row is None:
            return None
        return parse_embedding_json(row.embedding_json)

    def ensure_product_embedding(self, product: Product) -> Optional[list[float]]:
        existing = self.get_vector(product.id)
        if existing is not None:
            return existing
        if not settings.ai_enabled:
            return None
        try:
            vec = self.client.embed(product_embed_text(product))
        except OllamaError as exc:
            logger.warning("embed product %s failed: %s", product.id, exc)
            return None
        self._save(product.id, vec)
        return vec

    def _save(self, product_id: int, vec: list[float]) -> None:
        row = self.db.get(ProductEmbedding, product_id)
        payload = json.dumps(vec)
        model = settings.ollama_embed_model
        if row is None:
            self.db.add(ProductEmbedding(product_id=product_id, model=model, embedding_json=payload))
        else:
            row.model = model
            row.embedding_json = payload
        self.db.commit()
        self.invalidate_cache()

    def index_all_approved(self, limit: Optional[int] = None) -> int:
        stmt = (
            select(Product)
            .where(Product.status == "approved")
            .options(selectinload(Product.category))
            .order_by(Product.id.asc())
        )
        if limit:
            stmt = stmt.limit(limit)
        products = list(self.db.scalars(stmt).all())
        count = 0
        for p in products:
            if self.ensure_product_embedding(p):
                count += 1
        return count

    def _ensure_cache_loaded(self) -> dict[int, list[float]]:
        global _embedding_cache
        if _embedding_cache is not None:
            return _embedding_cache
        stmt = (
            select(ProductEmbedding.product_id, ProductEmbedding.embedding_json)
            .join(Product, Product.id == ProductEmbedding.product_id)
            .where(Product.status == "approved")
        )
        cache: dict[int, list[float]] = {}
        for pid, raw in self.db.execute(stmt).all():
            vec = parse_embedding_json(raw)
            if vec:
                cache[int(pid)] = vec
        _embedding_cache = cache
        return cache

    @staticmethod
    def invalidate_cache() -> None:
        global _embedding_cache
        _embedding_cache = None

    def similarity_search(
        self,
        query_vec: list[float],
        *,
        top_k: int = 20,
        exclude_ids: Optional[set[int]] = None,
    ) -> list[tuple[int, float]]:
        cache = self._ensure_cache_loaded()
        exclude = exclude_ids or set()
        scored: list[tuple[int, float]] = []
        for pid, vec in cache.items():
            if pid in exclude:
                continue
            scored.append((pid, cosine_similarity(query_vec, vec)))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def embed_query(self, text: str) -> Optional[list[float]]:
        if not settings.ai_enabled:
            return None
        try:
            return self.client.embed(text)
        except OllamaError:
            return None
