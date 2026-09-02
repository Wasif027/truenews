from __future__ import annotations

from datetime import datetime

from sqlmodel import Session, select

from app.ingest.sources import COUNTRIES
from app.models import Article, Cluster, Outlet
from app.schemas import OutletOut, StoryListItem


def outlet_out(o: Outlet) -> OutletOut:
    return OutletOut(slug=o.slug, name=o.name, homepage=o.homepage)


def first_articles(session: Session, clusters: list[Cluster]) -> dict[int, tuple[int, datetime]]:
    """cluster.first_article_id -> (outlet_id, published_at) in one query, so
    the list serializer isn't N+1. Column-select skips the big embedding vector."""
    ids = [c.first_article_id for c in clusters if c.first_article_id]
    if not ids:
        return {}
    rows = session.execute(
        select(Article.id, Article.outlet_id, Article.published_at).where(
            Article.id.in_(ids)  # type: ignore[attr-defined]
        )
    ).all()
    return {aid: (outlet_id, pub) for aid, outlet_id, pub in rows}


def list_item(
    c: Cluster,
    outlets: dict[int, Outlet],
    firsts: dict[int, tuple[int, datetime]],
) -> StoryListItem:
    first = firsts.get(c.first_article_id) if c.first_article_id else None
    first_outlet = outlets.get(first[0]) if first else None
    cats = [c.category] + ([c.category_secondary] if c.category_secondary else [])
    return StoryListItem(
        id=c.id,
        title=c.canonical_title,
        country=COUNTRIES.get(c.country, c.country.upper()),
        categories=cats,
        summary=c.summary,
        outlet_count=c.outlet_count,
        article_count=c.article_count,
        is_single_source=c.outlet_count <= 1,
        first_reported_by=outlet_out(first_outlet) if first_outlet else None,
        first_reported_at=first[1] if first else None,
        updated_at=c.updated_at,
        hotness=c.hotness,
    )
