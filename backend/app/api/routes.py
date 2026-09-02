from __future__ import annotations

import time
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlmodel import Session, select

from app.api.serializers import first_articles as _first_articles
from app.api.serializers import list_item as _list_item
from app.api.serializers import outlet_out as _outlet_out
from app.config import get_settings
from app.db import get_session
from app.models import Article, Cluster, FlaggedSentence, Outlet, utcnow
from app.schemas import (
    CategoryCount,
    SourceArticleOut,
    StatusOut,
    StoryDetail,
    StoryListItem,
)

router = APIRouter(prefix="/api")


@router.get("/_diag")
def _diag(session: Session = Depends(get_session)) -> dict:
    """Temporary: report whether the DB is reachable and why not. Remove once the
    deploy is confirmed healthy."""
    from app.config import get_settings as _gs

    url = _gs().database_url
    masked = url.split("@")[-1] if "@" in url else url
    try:
        n = session.exec(select(func.count()).select_from(Cluster)).one()
        return {"db": "ok", "clusters": n, "host": masked}
    except Exception as exc:  # noqa: BLE001
        return {"db": "error", "host": masked, "type": type(exc).__name__, "detail": str(exc)[:500]}


def _country(value: str | None) -> str:
    s = get_settings()
    return value if value in s.country_list else s.default_country


_outlet_cache: dict[str, object] = {"at": 0.0, "by_id": {}}


def _outlets(session: Session) -> dict[int, Outlet]:
    """Outlets change only during ingestion — cache them for a few minutes so
    every feed request isn't another round trip to the DB."""
    if time.monotonic() - _outlet_cache["at"] > 300 or not _outlet_cache["by_id"]:  # type: ignore[operator]
        _outlet_cache["by_id"] = {o.id: o for o in session.exec(select(Outlet))}
        _outlet_cache["at"] = time.monotonic()
    return _outlet_cache["by_id"]  # type: ignore[return-value]


@router.get("/stories", response_model=list[StoryListItem])
def list_stories(
    session: Session = Depends(get_session),
    country: str | None = None,
    category: str | None = None,
    q: str | None = None,
    min_outlets: int = Query(1, ge=1),
    sort: str = Query("hot", pattern="^(hot|new)$"),
    window_hours: int = Query(96, ge=1, le=720),
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    stmt = select(Cluster).where(
        Cluster.country == _country(country),
        Cluster.article_count > 0,
        Cluster.updated_at >= utcnow() - timedelta(hours=window_hours),
        Cluster.outlet_count >= min_outlets,
    )
    cats = [c.strip() for c in (category or "").split(",") if c.strip()]
    if cats:
        stmt = stmt.where(
            Cluster.category.in_(cats)  # type: ignore[attr-defined]
            | Cluster.category_secondary.in_(cats)  # type: ignore[attr-defined]
        )
    if q:
        like = f"%{q.strip()}%"
        matched = select(Article.cluster_id).where(
            Article.cluster_id.is_not(None), Article.headline.ilike(like)  # type: ignore[attr-defined]
        )
        stmt = stmt.where(
            Cluster.canonical_title.ilike(like)  # type: ignore[attr-defined]
            | Cluster.summary.ilike(like)  # type: ignore[attr-defined]
            | Cluster.id.in_(matched)  # type: ignore[attr-defined]
        )
    stmt = stmt.order_by(
        Cluster.hotness.desc() if sort == "hot" else Cluster.updated_at.desc()  # type: ignore[attr-defined]
    ).offset(offset).limit(limit)

    clusters = session.exec(stmt).all()
    outlets = _outlets(session)
    firsts = _first_articles(session, clusters)
    return [_list_item(c, outlets, firsts) for c in clusters]


@router.get("/stories/{story_id}", response_model=StoryDetail)
def get_story(
    story_id: int,
    session: Session = Depends(get_session),
):
    cluster = session.get(Cluster, story_id)
    if cluster is None or cluster.article_count == 0:
        raise HTTPException(status_code=404, detail="story not found")

    outlets = _outlets(session)
    country_outlets = [o for o in outlets.values() if o.country == cluster.country]
    # Column-select — never pull the per-article embedding vector into the API.
    arts = session.execute(
        select(
            Article.id, Article.outlet_id, Article.url, Article.headline,
            Article.byline, Article.published_at,
        )
        .where(Article.cluster_id == story_id)
        .order_by(Article.published_at)  # type: ignore[arg-type]
    ).all()

    flags_by_article: dict[int, list[str]] = {}
    if arts:
        for fs in session.exec(
            select(FlaggedSentence).where(FlaggedSentence.article_id.in_([a.id for a in arts]))  # type: ignore[attr-defined]
        ):
            flags_by_article.setdefault(fs.article_id, []).append(fs.text)

    first_id = cluster.first_article_id
    sources = [
        SourceArticleOut(
            id=a.id,
            outlet=_outlet_out(outlets[a.outlet_id]),
            url=a.url,
            headline=a.headline,
            byline=a.byline,
            published_at=a.published_at,
            is_first=(a.id == first_id),
            flagged_sentences=flags_by_article.get(a.id, []),
        )
        for a in arts
    ]
    reported = sorted({outlets[a.outlet_id].slug for a in arts})  # a.outlet_id via Row
    not_reporting = sorted({o.slug for o in country_outlets} - set(reported))

    base = _list_item(cluster, outlets, _first_articles(session, [cluster])).model_dump()
    return StoryDetail(
        **base,
        coverage_diff=cluster.coverage_diff,
        coverage_detail=cluster.coverage_detail,
        coverage={"reported": reported, "not_reporting": not_reporting},
        sources=sources,
    )


@router.get("/categories", response_model=list[CategoryCount])
def categories(
    session: Session = Depends(get_session),
    country: str | None = None,
    min_outlets: int = Query(1, ge=1),
):
    # Counts must track whatever filter the feed is showing, so "Hide
    # single-source" makes the tab numbers drop in step with the list.
    counts: dict[str, int] = {}
    for col in (Cluster.category, Cluster.category_secondary):
        for cat, n in session.execute(
            select(col, func.count())
            .where(
                Cluster.country == _country(country),
                Cluster.article_count > 0,
                Cluster.outlet_count >= min_outlets,
                col.is_not(None),
            )
            .group_by(col)
        ).all():
            counts[cat] = counts.get(cat, 0) + n
    ordered = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
    return [CategoryCount(category=c, count=n) for c, n in ordered]


@router.get("/countries")
def list_countries():
    from app.ingest.sources import COUNTRIES

    s = get_settings()
    return [{"code": c, "name": COUNTRIES.get(c, c.upper())} for c in s.country_list]


@router.get("/outlets")
def list_outlets(session: Session = Depends(get_session), country: str | None = None):
    """The outlets TrueNews reads for a country. Draws on the live DB first (so a
    just-added source shows once it has been ingested), falling back to the
    static config for outlets not yet fetched."""
    from app.ingest.sources import sources_for

    co = _country(country)
    seen = {
        o.slug: {"slug": o.slug, "name": o.name, "homepage": o.homepage}
        for o in session.exec(select(Outlet).where(Outlet.country == co))
    }
    for cfg in sources_for(co):
        seen.setdefault(
            cfg.slug, {"slug": cfg.slug, "name": cfg.name, "homepage": cfg.homepage}
        )
    return sorted(seen.values(), key=lambda o: o["name"].lower())


@router.get("/status", response_model=StatusOut)
def status(session: Session = Depends(get_session), country: str | None = None):
    s = get_settings()
    co = _country(country)

    def count(model, *where) -> int:
        return session.scalar(select(func.count()).select_from(model).where(*where)) or 0

    return StatusOut(
        country=co,
        outlets=count(Outlet, Outlet.country == co),
        articles=count(Article, Article.country == co),
        stories=count(Cluster, Cluster.country == co, Cluster.article_count > 0),
        last_story_update=session.scalar(
            select(func.max(Cluster.updated_at)).where(Cluster.country == co)
        ),
        window_hours=s.cluster_window_hours,
        sim_threshold=s.cluster_sim_threshold,
        llm_enabled=bool(s.llm_providers),
    )
