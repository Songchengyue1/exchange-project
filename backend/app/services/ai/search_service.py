from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.repositories.product import ProductRepository, SORT_MAP
from app.repositories.settings import SettingsRepository
from app.schemas.ai import AISearchOut
from app.services.ai.embedding_index import EmbeddingIndexService
from app.services.ai.llm_parse import SearchSlots, parse_search_query
from app.services.ai.ollama_client import OllamaClient
from app.services.product_serializers import serialize_product_list_item

logger = logging.getLogger(__name__)


class AISearchService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.products = ProductRepository(db)
        self.embeddings = EmbeddingIndexService(db)
        self.client = OllamaClient()

    def search(
        self,
        query: str,
        *,
        page: int = 1,
        page_size: int = 12,
    ) -> AISearchOut:
        hot = SettingsRepository(self.db).hot_rating_threshold()
        q = query.strip()
        used_llm = False
        fallback = False
        mode: str = "hybrid"

        slots: Optional[SearchSlots] = None
        if settings.ai_search_use_llm and self.client.is_available():
            slots = parse_search_query(q, client=self.client)
            used_llm = slots is not None

        keyword_q = (slots.q if slots and slots.q else q) or q
        category_id = slots.category_id if slots else None
        sort = slots.sort if slots and slots.sort in SORT_MAP else "created_at_desc"

        vector_ids: list[int] = []
        if settings.ai_enabled and self.client.is_available():
            qvec = self.embeddings.embed_query(q)
            if qvec:
                vector_ids = [pid for pid, _ in self.embeddings.similarity_search(qvec, top_k=50)]

        kw_rows, kw_total = self.products.list_marketplace(
            page=1,
            page_size=100,
            category_id=category_id,
            q=keyword_q,
            sort=sort,
        )

        if slots and (slots.price_min is not None or slots.price_max is not None):
            filtered = []
            for p in kw_rows:
                price = float(p.price)
                if slots.price_min is not None and price < slots.price_min:
                    continue
                if slots.price_max is not None and price > slots.price_max:
                    continue
                filtered.append(p)
            kw_rows = filtered

        merged_ids: list[int] = []
        seen: set[int] = set()
        for pid in vector_ids:
            if pid not in seen:
                seen.add(pid)
                merged_ids.append(pid)
        for p in kw_rows:
            if p.id not in seen:
                seen.add(p.id)
                merged_ids.append(p.id)

        if not merged_ids and not self.client.is_available():
            fallback = True
            mode = "keyword"
            rows, total = self.products.list_marketplace(
                page=page,
                page_size=page_size,
                q=q,
                sort="created_at_desc",
            )
            items = [serialize_product_list_item(p, hot_threshold=hot) for p in rows]
            return AISearchOut(
                items=items,
                total=total,
                page=page,
                page_size=page_size,
                mode=mode,
                used_llm=used_llm,
                fallback=fallback,
            )

        if not merged_ids:
            fallback = True
            mode = "keyword"
            rows, total = self.products.list_marketplace(page=page, page_size=page_size, q=q)
            items = [serialize_product_list_item(p, hot_threshold=hot) for p in rows]
            return AISearchOut(
                items=items,
                total=total,
                page=page,
                page_size=page_size,
                mode=mode,
                used_llm=used_llm,
                fallback=fallback,
            )

        if vector_ids and kw_rows:
            mode = "hybrid"
        elif vector_ids:
            mode = "vector"
        else:
            mode = "keyword"

        total = len(merged_ids)
        start = (page - 1) * page_size
        page_ids = merged_ids[start : start + page_size]
        id_order = {pid: i for i, pid in enumerate(page_ids)}
        loaded = []
        for pid in page_ids:
            p = self.products.get_detail(pid)
            if p and p.status == "approved":
                loaded.append(p)
        loaded.sort(key=lambda p: id_order.get(p.id, 999))
        items = [serialize_product_list_item(p, hot_threshold=hot) for p in loaded]
        return AISearchOut(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            mode=mode,
            used_llm=used_llm,
            fallback=fallback,
        )
