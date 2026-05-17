from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.review import Review
from app.models.user import User


def refresh_seller_rating(db: Session, seller_id: int) -> None:
    avg = db.scalar(
        select(func.avg(Review.rating)).where(Review.seller_id == seller_id)
    )
    user = db.get(User, seller_id)
    if user is None:
        return
    user.rating_avg = round(float(avg), 2) if avg is not None else None
    db.add(user)
