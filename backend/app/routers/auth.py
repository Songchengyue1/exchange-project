from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.database import get_db
from app.models.user import User
from app.repositories import UserRepository
from app.schemas.user import TokenResponse, UserCreate, UserLogin, UserPublic

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> TokenResponse:
    users = UserRepository(db)
    username = payload.username.strip()
    if users.username_exists(username):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="用户名已存在")
    user = users.create(
        User(
            username=username,
            password_hash=hash_password(payload.password),
            nickname=username,
            role="user",
        )
    )
    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token, user=UserPublic.model_validate(user))


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)) -> TokenResponse:
    user = UserRepository(db).get_by_username(payload.username.strip())
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    if user.is_disabled:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已被禁用")
    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token, user=UserPublic.model_validate(user))
