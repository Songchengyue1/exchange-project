from __future__ import annotations

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token_sub
from app.database import get_db
from app.models.user import User

security = HTTPBearer(auto_error=False)


def get_token_string(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> str:
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录或凭证无效",
        )
    return credentials.credentials


def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(get_token_string),
) -> User:
    sub = decode_token_sub(token)
    if sub is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="凭证无效或已过期")
    try:
        user_id = int(sub)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="凭证无效")
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")
    if user.is_disabled:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已被禁用")
    return user


def get_current_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    return user


def get_optional_user(
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[User]:
    if credentials is None or not credentials.credentials:
        return None
    sub = decode_token_sub(credentials.credentials)
    if sub is None:
        return None
    try:
        user_id = int(sub)
    except ValueError:
        return None
    user = db.get(User, user_id)
    if user is None or user.is_disabled:
        return None
    return user
