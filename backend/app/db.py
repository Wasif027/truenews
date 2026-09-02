from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import text
from sqlmodel import Session, SQLModel, create_engine

from app.config import get_settings

_settings = get_settings()
engine = create_engine(
    _settings.database_url,
    pool_pre_ping=True,
    # Neon (and most managed Postgres) drop idle connections and cold-start after
    # auto-suspend. Recycle before they do, and fail a stalled connect in 15s
    # instead of hanging.
    pool_recycle=280,
    connect_args={"connect_timeout": 15},
)


# Schema tweaks made after the first release. create_all() never ALTERs an
# existing table, so apply them here — all idempotent, cheap to run every boot.
_MIGRATIONS = (
    "ALTER TABLE article ADD COLUMN IF NOT EXISTS category_secondary VARCHAR",
    "ALTER TABLE cluster ADD COLUMN IF NOT EXISTS category_secondary VARCHAR",
    "ALTER TABLE cluster ADD COLUMN IF NOT EXISTS coverage_detail VARCHAR",
    # feed query, sort=hot: filter by country, order by hotness desc, limit
    "CREATE INDEX IF NOT EXISTS ix_cluster_feed ON cluster (country, hotness DESC)",
    # feed query, sort=new + the 96h recency filter on every feed request
    "CREATE INDEX IF NOT EXISTS ix_cluster_recency ON cluster (country, updated_at DESC)",
)


def init_db() -> None:
    """Create the pgvector extension and all tables. Fine for a portfolio project;
    swap for Alembic migrations if the schema starts churning."""
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    # Import models so they are registered on SQLModel.metadata before create_all.
    from app import models  # noqa: F401

    SQLModel.metadata.create_all(engine)

    with engine.connect() as conn:
        for stmt in _MIGRATIONS:
            conn.execute(text(stmt))
        conn.commit()


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session
