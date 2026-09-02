from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlmodel import Session, select

from app.config import get_settings
from app.db import get_session
from app.models import User
from app.security import (
    COOKIE_NAME,
    get_current_user,
    hash_password,
    make_token,
    verify_password,
)

router = APIRouter(prefix="/api/auth")

_USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,20}$")


class Credentials(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    username: str


def _set_cookie(response: Response, user_id: int) -> None:
    s = get_settings()
    response.set_cookie(
        COOKIE_NAME,
        make_token(user_id),
        max_age=s.token_ttl_days * 86400,
        httponly=True,
        samesite="lax",
        secure=s.cookie_secure,
        path="/",
    )


@router.post("/signup", response_model=UserOut)
def signup(body: Credentials, response: Response, session: Session = Depends(get_session)):
    username = body.username.strip()
    if not _USERNAME_RE.match(username):
        raise HTTPException(422, "username must be 3-20 letters, numbers or underscore")
    if len(body.password) < 8:
        raise HTTPException(422, "password must be at least 8 characters")
    if session.exec(select(User).where(User.username == username)).first():
        raise HTTPException(409, "username taken")

    user = User(username=username, password_hash=hash_password(body.password))
    session.add(user)
    session.commit()
    session.refresh(user)
    _set_cookie(response, user.id)
    return UserOut(username=user.username)


@router.post("/login", response_model=UserOut)
def login(body: Credentials, response: Response, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.username == body.username.strip())).first()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "wrong username or password")
    _set_cookie(response, user.id)
    return UserOut(username=user.username)


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"ok": True}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return UserOut(username=user.username)
