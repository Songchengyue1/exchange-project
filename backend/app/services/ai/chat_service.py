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
from app.services.ai.query_terms import expand_search_terms, is_browse_all_intent, product_links_kind

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "你是酱菜交易平台 AI 助手。只能依据下方「相关商品」列表作答，用一两句中文说明是否有货、名称与价格。"
    "列表中有「- 商品名」条目时，表示有匹配商品，必须按列表回答，禁止说「暂无匹配」。"
    "仅当列表仅为「（暂无）」时，才可以说暂无匹配。"
    "不要编造列表外的商品；用户说苹果手机时，列表中的 iPhone 即视为匹配。"
)

_NO_MATCH_HINTS = ("暂无匹配", "暂无相关", "没有匹配", "未找到", "找不到", "无相关商品", "无匹配")

_HISTORY_TRIM = 280


class AIChatService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.conversations = AIConversationRepository(db)
        self.embeddings = EmbeddingIndexService(db)
        self.client = OllamaClient()

    def _keyword_retrieve(self, query: str, top_k: int) -> list[int]:
        repo = ProductRepository(self.db)
        terms = expand_search_terms(query)
        ids: list[int] = []
        seen: set[int] = set()

        for term in terms:
            rows, _ = repo.list_marketplace(page=1, page_size=top_k, q=term)
            for p in rows:
                if p.id not in seen:
                    seen.add(p.id)
                    ids.append(p.id)
            if len(ids) >= top_k:
                break

        if not ids and is_browse_all_intent(query):
            rows, _ = repo.list_marketplace(page=1, page_size=top_k)
            ids = [p.id for p in rows]

        return ids[:top_k]

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

    def _products_payload(self, products: list[Product], query: str) -> dict:
        kind = product_links_kind(query)
        refs = [{"id": p.id, "title": p.title} for p in products]
        return {
            "product_ids": [p.id for p in products],
            "product_refs": refs,
            "products_kind": kind,
        }

    def _products_meta_json(self, products: list[Product], query: str) -> str:
        return json.dumps(self._products_payload(products, query), ensure_ascii=False)

    def _format_product_context(self, products: list[Product]) -> str:
        if not products:
            return "（暂无）"
        lines = []
        for p in products:
            cat = p.category.name if p.category else ""
            lines.append(f"- {p.title} ¥{float(p.price):.0f} {cat}")
        return "\n".join(lines)

    def _looks_like_false_no_match(self, text: str) -> bool:
        t = text.strip().replace(" ", "")
        if not t:
            return True
        if len(t) > 120:
            return False
        return any(h in t for h in _NO_MATCH_HINTS)

    def _template_reply_from_products(self, products: list[Product]) -> str:
        if len(products) == 1:
            p = products[0]
            return f"有货。{p.title}，价格 ¥{float(p.price):.0f}。"
        lines = ["有货，相关商品如下："]
        for p in products[:4]:
            lines.append(f"- {p.title} ¥{float(p.price):.0f}")
        return "\n".join(lines)

    def _finalize_assistant_reply(self, text: str, products: list[Product]) -> str:
        cleaned = text.strip()
        if not products:
            if cleaned:
                return cleaned
            return "暂未找到相关商品，可到商品页浏览。"
        if self._looks_like_false_no_match(cleaned):
            return self._template_reply_from_products(products)
        return cleaned

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

        payload = self._products_payload(products, text)
        yield {"event": "meta", "status": "generating", **payload}

        if not settings.ai_enabled:
            fallback = "AI 功能已关闭。"
            assistant = await asyncio.to_thread(
                self.conversations.add_message,
                conv.id,
                "assistant",
                fallback,
                self._products_meta_json(products, text),
            )
            yield {"event": "chunk", "content": fallback}
            yield {
                "event": "done",
                "conversation_id": conv.id,
                "assistant_message_id": assistant.id,
                **payload,
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
                self._products_meta_json(products, text),
            )
            yield {"event": "chunk", "content": fallback}
            yield {
                "event": "done",
                "conversation_id": conv.id,
                "assistant_message_id": assistant.id,
                **payload,
            }
            return

        full = "".join(full_parts).strip()
        full = self._finalize_assistant_reply(full, products)
        if not full:
            full = "抱歉，请换个说法或到商品页浏览。"

        assistant = await asyncio.to_thread(
            self.conversations.add_message,
            conv.id,
            "assistant",
            full,
            self._products_meta_json(products, text),
        )
        yield {
            "event": "done",
            "conversation_id": conv.id,
            "assistant_message_id": assistant.id,
            "content": full,
            **payload,
        }
