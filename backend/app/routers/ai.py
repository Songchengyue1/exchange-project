from __future__ import annotations

import json
from typing import AsyncIterator, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal, get_db
from app.deps import get_current_user, get_optional_user
from app.models.user import User
from app.repositories.ai import AIConversationRepository
from app.repositories.browse_history import BrowseHistoryRepository
from app.repositories.product import ProductRepository
from app.schemas.ai import (
    AIConversationDetail,
    AIConversationOut,
    AIMessageOut,
    AIProductRef,
    AISearchIn,
    AISearchOut,
    AIRecommendOut,
    BrowseRecordIn,
    ChatIn,
)
from app.services.ai.chat_service import AIChatService
from app.services.ai.embedding_index import EmbeddingIndexService
from app.services.ai.recommend_service import AIRecommendService
from app.services.ai.search_service import AISearchService

router = APIRouter(prefix="/ai", tags=["ai"])


def _message_to_out(msg) -> AIMessageOut:
    product_ids: list[int] = []
    product_refs: list[AIProductRef] = []
    products_kind: str | None = None
    if msg.meta_json:
        try:
            meta = json.loads(msg.meta_json)
            raw = meta.get("product_ids")
            if isinstance(raw, list):
                product_ids = []
                for x in raw:
                    try:
                        product_ids.append(int(x))
                    except (TypeError, ValueError):
                        continue
            refs = meta.get("product_refs")
            if isinstance(refs, list):
                for item in refs:
                    if not isinstance(item, dict):
                        continue
                    try:
                        pid = int(item.get("id"))
                        title = str(item.get("title") or f"商品 #{pid}")
                        product_refs.append(AIProductRef(id=pid, title=title))
                    except (TypeError, ValueError):
                        continue
            kind = meta.get("products_kind")
            if kind in ("target", "recommend"):
                products_kind = kind
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
    if not product_refs and product_ids:
        product_refs = [AIProductRef(id=pid, title=f"商品 #{pid}") for pid in product_ids]
    return AIMessageOut(
        id=msg.id,
        role=msg.role,
        content=msg.content,
        created_at=msg.created_at,
        product_ids=product_ids,
        product_refs=product_refs,
        products_kind=products_kind,
    )


@router.post("/browse", status_code=status.HTTP_204_NO_CONTENT)
def record_browse(
    body: BrowseRecordIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    product = ProductRepository(db).get_by_id(body.product_id)
    if product is None or product.status != "approved":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="商品不存在")
    BrowseHistoryRepository(db).record(user.id, body.product_id)


@router.get("/recommendations", response_model=AIRecommendOut)
def recommendations(
    limit: int = Query(8, ge=1, le=20),
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
) -> AIRecommendOut:
    uid = user.id if user else None
    return AIRecommendService(db).recommend(uid, limit=limit)


@router.post("/search", response_model=AISearchOut)
def ai_search(body: AISearchIn, db: Session = Depends(get_db)) -> AISearchOut:
    if body.page < 1 or body.page_size < 1 or body.page_size > 50:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="分页参数无效")
    return AISearchService(db).search(body.query, page=body.page, page_size=body.page_size)


@router.post("/embeddings/reindex")
def reindex_embeddings(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    count = EmbeddingIndexService(db).index_all_approved()
    return {"indexed": count}


@router.get("/conversations", response_model=list[AIConversationOut])
def list_conversations(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[AIConversationOut]:
    rows = AIConversationRepository(db).list_for_user(user.id)
    return [AIConversationOut.model_validate(r) for r in rows]


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    ok = AIConversationRepository(db).delete(conversation_id, user.id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")


@router.get("/conversations/{conversation_id}", response_model=AIConversationDetail)
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> AIConversationDetail:
    conv = AIConversationRepository(db).get(conversation_id, user.id)
    if conv is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")
    return AIConversationDetail(
        id=conv.id,
        title=conv.title,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        messages=[_message_to_out(m) for m in conv.messages],
    )


def _sse_line(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/chat")
async def chat_stream(
    body: ChatIn,
    user: User = Depends(get_current_user),
) -> StreamingResponse:
    if not settings.ai_enabled:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AI 功能已关闭")

    async def generate() -> AsyncIterator[str]:
        db = SessionLocal()
        try:
            service = AIChatService(db)
            async for payload in service.stream_reply(
                user.id,
                body.message,
                conversation_id=body.conversation_id,
            ):
                event = payload.get("event", "message")
                yield _sse_line(event, payload)
        finally:
            db.close()

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
