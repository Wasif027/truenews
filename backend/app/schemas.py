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


class OutletLeanOut(BaseModel):
    outlet: str
    lean: str
    confidence: str  # "low" | "medium" | "high"
    evidence: list[str] = []
    loaded_language: list[str] = []


class CompareSourceOut(BaseModel):
    outlet: str
    title: str
    url: str
    published_at: str | None = None
    lean: OutletLeanOut | None = None


class CompareResultOut(BaseModel):
    relation: str  # "same_event" | "related" | "unrelated"
    relation_note: str | None = None
    shared_facts: str
    agreements: list[str] = []
    differences: list[str] = []
    consensus_slant: str | None = None
    blind_spots: list[str] = []
    takeaway: str
    via: str  # "llm" | "offline"
    sources: list[CompareSourceOut]
    unmatched_leans: list[OutletLeanOut] = []
    failed: list[dict] = []


class StatusOut(BaseModel):
    country: str
    outlets: int
    articles: int
    stories: int
    last_story_update: datetime | None
    window_hours: int
    sim_threshold: float
    llm_enabled: bool
