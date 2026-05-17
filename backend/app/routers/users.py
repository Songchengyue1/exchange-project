from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.repositories import UserRepository
from app.schemas.user import UserPublic, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
EXT_BY_TYPE = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
MAX_AVATAR_BYTES = 2 * 1024 * 1024


@router.get("/me", response_model=UserPublic)
def read_me(user: User = Depends(get_current_user)) -> User:
    return user


@router.patch("/me", response_model=UserPublic)
def update_me(
    payload: UserUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> User:
    data = payload.model_dump(exclude_unset=True)
    if "nickname" in data and data["nickname"] is not None:
        data["nickname"] = data["nickname"].strip()
        if not data["nickname"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="昵称不能为空")
    for key in ("phone", "address"):
        if key in data and data[key] is not None and str(data[key]).strip() == "":
            data[key] = None
    for key, value in data.items():
        setattr(user, key, value)
    return UserRepository(db).save(user)


@router.post("/me/avatar", response_model=UserPublic)
async def upload_avatar(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    file: UploadFile = File(...),
) -> User:
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="仅支持 JPG / PNG / WEBP")
    body = await file.read()
    if len(body) > MAX_AVATAR_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="图片不能超过 2MB")
    ext = EXT_BY_TYPE[file.content_type]
    upload_dir = Path("uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    name = f"{user.id}_{uuid.uuid4().hex}{ext}"
    path = upload_dir / name
    path.write_bytes(body)
    user.avatar_url = f"/static/{name}"
    return UserRepository(db).save(user)
