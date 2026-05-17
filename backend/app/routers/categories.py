from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories import CategoryRepository
from app.schemas.category import CategoryPublic

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryPublic])
def list_categories(db: Session = Depends(get_db)) -> list[CategoryPublic]:
    rows = CategoryRepository(db).list_all()
    return [CategoryPublic.model_validate(c) for c in rows]
