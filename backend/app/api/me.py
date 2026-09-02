from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.api.serializers import first_articles, list_item
from app.db import get_session
from app.models import Cluster, Like, Outlet, Save, User, Visit
from app.schemas import StoryListItem
from app.security import get_current_user, get_optional_user

router = APIRouter(prefix="/api")

HISTORY_LIMIT = 20


def _toggle(session: Session, model, user_id: int, cluster_id: int, on: bool) -> dict:
    existing = session.exec(
        select(model).where(model.user_id == user_id, model.cluster_id == cluster_id)
    ).first()
    if on and existing is None:
        session.add(model(user_id=user_id, cluster_id=cluster_id))
    elif not on and existing is not None:
        session.delete(existing)
    session.commit()
    return {"on": on}


def _stories_for(session: Session, cluster_ids: list[int]) -> list[StoryListItem]:
    if not cluster_ids:
        return []
    outlets = {o.id: o for o in session.exec(select(Outlet))}
    by_id = {
        c.id: c
        for c in session.exec(select(Cluster).where(Cluster.id.in_(cluster_ids)))  # type: ignore[attr-defined]
        if c.article_count > 0
    }
    firsts = first_articles(session, list(by_id.values()))
    return [list_item(by_id[cid], outlets, firsts) for cid in cluster_ids if cid in by_id]


@router.get("/stories/{story_id}/me")
def my_flags(
    story_id: int,
    session: Session = Depends(get_session),
    user: User | None = Depends(get_optional_user),
) -> dict:
    """Whether the current user has liked/saved this story. Split out of the
    story payload so the story page itself can be cached."""
    if user is None:
        return {"liked": False, "saved": False}
    liked = session.exec(
        select(Like).where(Like.user_id == user.id, Like.cluster_id == story_id)
    ).first()
    saved = session.exec(
        select(Save).where(Save.user_id == user.id, Save.cluster_id == story_id)
    ).first()
    return {"liked": liked is not None, "saved": saved is not None}


@router.put("/stories/{story_id}/like")
def set_like(
    story_id: int,
    on: bool = True,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    return _toggle(session, Like, user.id, story_id, on)


@router.put("/stories/{story_id}/save")
def set_save(
    story_id: int,
    on: bool = True,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    return _toggle(session, Save, user.id, story_id, on)


@router.post("/stories/{story_id}/visit")
def record_visit(
    story_id: int,
    session: Session = Depends(get_session),
    user: User = Depends(get_current_user),
):
    session.add(Visit(user_id=user.id, cluster_id=story_id))
    session.commit()
    # keep only the most recent HISTORY_LIMIT per user
    stale = session.exec(
        select(Visit)
        .where(Visit.user_id == user.id)
        .order_by(Visit.visited_at.desc())  # type: ignore[attr-defined]
        .offset(HISTORY_LIMIT)
    ).all()
    for v in stale:
        session.delete(v)
    if stale:
        session.commit()
    return {"ok": True}


@router.get("/me/likes", response_model=list[StoryListItem])
def my_likes(session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    ids = session.exec(
        select(Like.cluster_id).where(Like.user_id == user.id).order_by(Like.created_at.desc())  # type: ignore[attr-defined]
    ).all()
    return _stories_for(session, list(ids))


@router.get("/me/saves", response_model=list[StoryListItem])
def my_saves(session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    ids = session.exec(
        select(Save.cluster_id).where(Save.user_id == user.id).order_by(Save.created_at.desc())  # type: ignore[attr-defined]
    ).all()
    return _stories_for(session, list(ids))


@router.get("/me/history", response_model=list[StoryListItem])
def my_history(session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    ids: list[int] = []
    for cid in session.exec(
        select(Visit.cluster_id)
        .where(Visit.user_id == user.id)
        .order_by(Visit.visited_at.desc())  # type: ignore[attr-defined]
    ):
        if cid not in ids:  # collapse repeat visits
            ids.append(cid)
    return _stories_for(session, ids[:HISTORY_LIMIT])
