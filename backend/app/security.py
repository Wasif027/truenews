from __future__ import annotations

from datetime import timedelta

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Request
from sqlmodel import Session

from app.config import get_settings
from app.db import get_session
from app.models import User, utcnow

COOKIE_NAME = "tn_token"
_ALG = "HS256"


def hash_password(raw: str) -> str:
    return bcrypt.hashpw(raw.encode(), bcrypt.gensalt()).decode()


def verify_password(raw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(raw.encode(), hashed.encode())
    except ValueError:
        return False


def make_token(user_id: int) -> str:
    s = get_settings()
    now = utcnow()
    payload = {"sub": str(user_id), "iat": now, "exp": now + timedelta(days=s.token_ttl_days)}
    return jwt.encode(payload, s.secret_key, algorithm=_ALG)


def _user_id_from_token(token: str) -> int | None:
    try:
        payload = jwt.decode(token, get_settings().secret_key, algorithms=[_ALG])
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None


def get_optional_user(
    request: Request, session: Session = Depends(get_session)
) -> User | None:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    uid = _user_id_from_token(token)
    return session.get(User, uid) if uid is not None else None


def get_current_user(user: User | None = Depends(get_optional_user)) -> User:
    if user is None:
        raise HTTPException(status_code=401, detail="not signed in")
    return user
