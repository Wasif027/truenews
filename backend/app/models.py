from __future__ import annotations

from datetime import UTC, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, DateTime, UniqueConstraint
from sqlmodel import Field, SQLModel

from app.config import get_settings

_DIM = get_settings().embedding_dim
_TZ = DateTime(timezone=True)  # keep timestamps tz-aware end to end


def utcnow() -> datetime:
    return datetime.now(UTC)


class Outlet(SQLModel, table=True):
    __tablename__ = "outlet"

    id: int | None = Field(default=None, primary_key=True)
    country: str = Field(index=True)
    slug: str = Field(unique=True)
    name: str
    homepage: str
    rss_url: str


class Article(SQLModel, table=True):
    __tablename__ = "article"
    __table_args__ = (UniqueConstraint("url", name="uq_article_url"),)

    id: int | None = Field(default=None, primary_key=True)
    outlet_id: int = Field(foreign_key="outlet.id", index=True)
    country: str = Field(index=True)
    url: str
    headline: str
    byline: str | None = None
    lead_text: str = ""
    category: str = Field(default="general", index=True)
    category_secondary: str | None = Field(default=None, index=True)
    published_at: datetime = Field(sa_type=_TZ, index=True)
    fetched_at: datetime = Field(default_factory=utcnow, sa_type=_TZ)
    embedding: list[float] | None = Field(default=None, sa_column=Column(Vector(_DIM)))
    cluster_id: int | None = Field(default=None, foreign_key="cluster.id", index=True)


class Cluster(SQLModel, table=True):
    __tablename__ = "cluster"

    id: int | None = Field(default=None, primary_key=True)
    country: str = Field(index=True)
    canonical_title: str
    category: str = Field(default="general", index=True)
    category_secondary: str | None = Field(default=None, index=True)
    created_at: datetime = Field(default_factory=utcnow, sa_type=_TZ, index=True)
    updated_at: datetime = Field(default_factory=utcnow, sa_type=_TZ, index=True)
    # Plain id, not a FK: article <-> cluster would be a circular FK and
    # SQLModel.metadata.create_all() cannot order that without ALTER.
    first_article_id: int | None = None
    outlet_count: int = 0
    article_count: int = 0
    hotness: float = Field(default=0.0, index=True)

    summary: str | None = None
    coverage_diff: str | None = None
    # Longer, per-outlet "how each outlet handled it" breakdown (LLM only).
    coverage_detail: str | None = None
    # Set of outlet ids the summary was generated against, so we only re-summarise
    # when the coverage set actually changes.
    summarised_outlet_ids: str | None = None


class FlaggedSentence(SQLModel, table=True):
    __tablename__ = "flagged_sentence"

    id: int | None = Field(default=None, primary_key=True)
    article_id: int = Field(foreign_key="article.id", index=True)
    text: str
    score: float


class User(SQLModel, table=True):
    __tablename__ = "app_user"  # "user" is reserved in Postgres

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    password_hash: str
    created_at: datetime = Field(default_factory=utcnow, sa_type=_TZ)


class Like(SQLModel, table=True):
    __tablename__ = "like"
    __table_args__ = (UniqueConstraint("user_id", "cluster_id", name="uq_like"),)

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="app_user.id", index=True)
    cluster_id: int = Field(index=True)
    created_at: datetime = Field(default_factory=utcnow, sa_type=_TZ, index=True)


class Save(SQLModel, table=True):
    __tablename__ = "save"
    __table_args__ = (UniqueConstraint("user_id", "cluster_id", name="uq_save"),)

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="app_user.id", index=True)
    cluster_id: int = Field(index=True)
    created_at: datetime = Field(default_factory=utcnow, sa_type=_TZ, index=True)


class Visit(SQLModel, table=True):
    __tablename__ = "visit"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="app_user.id", index=True)
    cluster_id: int
    visited_at: datetime = Field(default_factory=utcnow, sa_type=_TZ, index=True)
