from __future__ import annotations

import asyncio
import json
import logging
from typing import AsyncIterator, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.config import settings
from app.models.product import Product
from app.repositories.ai import AIConversationRepository
from app.repositories.product import ProductRepository
from app.services.ai.embedding_index import EmbeddingIndexService
from app.services.ai.ollama_client import OllamaClient, OllamaError

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "你是酱菜交易平台 AI 助手。仅根据「相关商品」列表用简短中文回答，可列商品名与价格。"
    "列表为空则说明暂无匹配。不要编造商品，勿长篇科普站外平台。"
)

_HISTORY_TRIM = 280
_KEYWORD_HINTS = ("mac", "iphone", "电脑", "手机", "书", "桌", "鞋", "switch", "宜家")


class AIChatService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.conversations = AIConversationRepository(db)
        self.embeddings = EmbeddingIndexService(db)
        self.client = OllamaClient()

    def _keyword_retrieve(self, query: str, top_k: int) -> list[int]:
        repo = ProductRepository(self.db)
        q = query.strip()
        rows, _ = repo.list_marketplace(page=1, page_size=top_k, q=q or None)
        if not rows and q:
            low = q.lower()
            for token in _KEYWORD_HINTS:
                if token in low:
                    rows, _ = repo.list_marketplace(page=1, page_size=top_k, q=token)
                    if rows:
                        break
        if not rows:
            rows, _ = repo.list_marketplace(page=1, page_size=top_k)
        return [p.id for p in rows]

    def _vector_retrieve(self, query: str, top_k: int) -> list[int]:
        qvec = self.embeddings.embed_query(query)
        if not qvec:
            return []
        return [pid for pid, _ in self.embeddings.similarity_search(qvec, top_k=top_k)]

    def _retrieve_products(self, query: str, top_k: int = 4) -> list[Product]:
        ids: list[int] = []
        if settings.ai_chat_keyword_first:
            ids = self._keyword_retrieve(query, top_k)
        if settings.ai_chat_use_vector or (not ids and not settings.ai_chat_keyword_first):
            vec_ids = self._vector_retrieve(query, top_k)
            for pid in vec_ids:
                if pid not in ids:
                    ids.append(pid)
            ids = ids[:top_k]
        if not ids:
            return []

        stmt = (
            select(Product)
            .where(Product.id.in_(ids), Product.status == "approved")
            .options(selectinload(Product.category))
        )
        by_id = {p.id: p for p in self.db.scalars(stmt).all()}
        return [by_id[i] for i in ids if i in by_id]

    def _format_product_context(self, products: list[Product]) -> str:
        if not products:
            return "（暂无）"
        lines = []
        for p in products:
            cat = p.category.name if p.category else ""
            lines.append(f"- {p.title} ¥{float(p.price):.0f} {cat}")
        return "\n".join(lines)

    def _build_messages(
        self,
        history: list,
        user_text: str,
        context: str,
    ) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = [
            {"role": "system", "content": f"{SYSTEM_PROMPT}\n相关商品：\n{context}"},
        ]
        limit = max(0, settings.ai_chat_max_history)
        for m in history[-limit:]:
            if m.role not in ("user", "assistant"):
                continue
            body = (m.content or "").strip()
            if m.role == "assistant" and len(body) > _HISTORY_TRIM:
                body = body[:_HISTORY_TRIM] + "…"
            messages.append({"role": m.role, "content": body})
        messages.append({"role": "user", "content": user_text})
        return messages

    def _prepare_turn(
        self,
        user_id: int,
        text: str,
        conversation_id: Optional[int],
    ) -> tuple[object, list[Product], list[dict[str, str]], list]:
        conv = None
        if conversation_id:
            conv = self.conversations.get(conversation_id, user_id)
        if conv is None:
            title = text[:40] + ("…" if len(text) > 40 else "")
            conv = self.conversations.create(user_id, title=title)
        else:
            self.conversations.touch(conv)

        history = self.conversations.recent_messages(conv.id, limit=settings.ai_chat_max_history + 2)
        self.conversations.add_message(conv.id, "user", text)
        products = self._retrieve_products(text)
        context = self._format_product_context(products)
        messages = self._build_messages(history, text, context)
        return conv, products, messages, history

    async def stream_reply(
        self,
        user_id: int,
        message: str,
        conversation_id: Optional[int] = None,
    ) -> AsyncIterator[dict]:
        text = message.strip()
        if not text:
            yield {"event": "error", "detail": "消息不能为空"}
            return

        yield {"event": "meta", "status": "retrieving"}

        try:
            conv, products, messages, _history = await asyncio.to_thread(
                self._prepare_turn,
                user_id,
                text,
                conversation_id,
            )
        except Exception as exc:
            logger.exception("chat prepare failed")
            yield {"event": "error", "detail": str(exc)}
            return

        product_ids = [p.id for p in products]
        yield {"event": "meta", "status": "generating", "product_ids": product_ids}

        if not settings.ai_enabled:
            fallback = "AI 功能已关闭。"
            assistant = await asyncio.to_thread(
                self.conversations.add_message,
                conv.id,
                "assistant",
                fallback,
                json.dumps({"product_ids": product_ids}),
            )
            yield {"event": "chunk", "content": fallback}
            yield {
                "event": "done",
                "conversation_id": conv.id,
                "assistant_message_id": assistant.id,
                "product_ids": product_ids,
            }
            return

        full_parts: list[str] = []
        try:
            async for chunk in self.client.achat_stream(messages):
                full_parts.append(chunk)
                yield {"event": "chunk", "content": chunk}
        except OllamaError as exc:
            # 无健康检查预检，失败时模板回复仍带商品信息
            titles = "、".join(p.title for p in products[:4])
            fallback = (
                f"模型暂时繁忙。当前找到：{titles or '暂无'}。"
                if products
                else "模型暂时繁忙，请稍后在商品列表浏览。"
            )
            assistant = await asyncio.to_thread(
                self.conversations.add_message,
                conv.id,
                "assistant",
                fallback,
                json.dumps({"product_ids": product_ids}),
            )
            yield {"event": "chunk", "content": fallback}
            yield {
                "event": "done",
                "conversation_id": conv.id,
                "assistant_message_id": assistant.id,
                "product_ids": product_ids,
            }
            return

        full = "".join(full_parts).strip()
        if not full and products:
            full = "相关商品：\n" + self._format_product_context(products)
        if not full:
            full = "抱歉，请换个说法或到商品页浏览。"

        assistant = await asyncio.to_thread(
            self.conversations.add_message,
            conv.id,
            "assistant",
            full,
            json.dumps({"product_ids": product_ids}),
        )
        yield {
            "event": "done",
            "conversation_id": conv.id,
            "assistant_message_id": assistant.id,
            "product_ids": product_ids,
        }
