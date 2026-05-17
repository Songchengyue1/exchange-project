from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.feedback import Feedback
from app.models.user import User
from app.repositories import FeedbackRepository
from app.schemas.feedback import FeedbackCreate, FeedbackPublic

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("", response_model=FeedbackPublic, status_code=status.HTTP_201_CREATED)
def submit_feedback(
    payload: FeedbackCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> FeedbackPublic:
    fb = FeedbackRepository(db).create(
        Feedback(
            user_id=user.id,
            subject=payload.subject.strip(),
            content=payload.content.strip(),
            status="pending",
        )
    )
    return FeedbackPublic.model_validate(fb)


@router.get("/mine", response_model=list[FeedbackPublic])
def list_my_feedback(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[FeedbackPublic]:
    rows = FeedbackRepository(db).list_by_user(user.id)
    return [FeedbackPublic.model_validate(f) for f in rows]
