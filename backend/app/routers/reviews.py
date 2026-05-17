from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.repositories import ReviewRepository
from app.schemas.review import ReviewPublic

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("/mine", response_model=list[ReviewPublic])
def list_my_reviews(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ReviewPublic]:
    rows = ReviewRepository(db).list_by_buyer(user.id)
    return [
        ReviewPublic(
            id=r.id,
            order_id=r.order_id,
            product_id=r.product_id,
            rating=r.rating,
            comment=r.comment,
            buyer_nickname=r.buyer.nickname,
            created_at=r.created_at,
        )
        for r in rows
    ]
