from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class OutletOut(BaseModel):
    slug: str
    name: str
    homepage: str


class SourceArticleOut(BaseModel):
    id: int
    outlet: OutletOut
    url: str
    headline: str
    byline: str | None
    published_at: datetime
    is_first: bool
    flagged_sentences: list[str] = []


class StoryListItem(BaseModel):
    id: int
    title: str
    country: str  # display name, e.g. "Bangladesh"
    categories: list[str]  # 1 or 2, most prominent first
    summary: str | None
    outlet_count: int
    article_count: int
    is_single_source: bool
    first_reported_by: OutletOut | None
    first_reported_at: datetime | None
    updated_at: datetime
    hotness: float


class StoryDetail(StoryListItem):
    coverage_diff: str | None
    coverage_detail: str | None = None
    coverage: dict  # {"reported": [slug...], "not_reporting": [slug...]}
    sources: list[SourceArticleOut]


class CategoryCount(BaseModel):
    category: str
    count: int


class StatusOut(BaseModel):
    country: str
    outlets: int
    articles: int
    stories: int
    last_story_update: datetime | None
    window_hours: int
    sim_threshold: float
    llm_enabled: bool
