from __future__ import annotations

import time
from collections import deque
from threading import Lock
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.schemas import CompareResultOut, CompareSourceOut, OutletLeanOut
from app.services.compare import BYOKError, CompareInput, compare_sources
from app.services.fetch_url import fetch_many

router = APIRouter(prefix="/api")

_MAX_URLS = 4
_MIN_URLS = 2

# Per-IP rate limit on the shared model pool. One Render instance, so an
# in-process window is enough; nothing here is worth a database table. A
# visitor using their own API key isn't drawing on that pool, so gets a looser
# limit — the article fetch is still our bandwidth, so still capped.
_RATE_MAX = 8
_RATE_MAX_BYOK = 30
_RATE_WINDOW = 3600.0
_hits: dict[str, deque[float]] = {}
_hits_lock = Lock()

# Short result cache so a page refresh doesn't re-fetch and re-bill the model.
_CACHE_TTL = 600.0
_cache: dict[frozenset[str], tuple[float, CompareResultOut]] = {}


class CompareRequest(BaseModel):
    urls: list[str] = Field(min_length=_MIN_URLS, max_length=_MAX_URLS)
    # Bring-your-own-key: used only for this one request, never logged or
    # stored server-side. `llm_key` is never echoed back in any response.
    llm_provider: Literal["gemini", "groq"] | None = None
    llm_key: str = Field(default="", max_length=200)


def _client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for", "")
    return fwd.split(",")[0].strip() if fwd else (request.client.host if request.client else "?")


def _rate_check(ip: str, *, byok: bool) -> None:
    limit = _RATE_MAX_BYOK if byok else _RATE_MAX
    now = time.monotonic()
    with _hits_lock:
        q = _hits.setdefault(f"{'k' if byok else 's'}:{ip}", deque())
        while q and now - q[0] > _RATE_WINDOW:
            q.popleft()
        if len(q) >= limit:
            raise HTTPException(429, f"Rate limit: {limit} comparisons per hour. Try again later.")
        q.append(now)


def _normalise(urls: list[str]) -> list[str]:
    seen: list[str] = []
    for u in urls:
        u = u.strip()
        if not u:
            continue
        if not u.startswith(("http://", "https://")):
            u = "https://" + u
        if u not in seen:
            seen.append(u)
    if len(seen) < _MIN_URLS:
        raise HTTPException(422, "Give at least two different article links.")
    return seen


@router.post("/compare", response_model=CompareResultOut)
def compare(body: CompareRequest, request: Request) -> CompareResultOut:
    urls = _normalise(body.urls)
    byok = (body.llm_provider, body.llm_key.strip()) if body.llm_provider and body.llm_key.strip() else None

    key = frozenset(urls)
    hit = _cache.get(key)
    if hit and time.monotonic() - hit[0] < _CACHE_TTL:
        return hit[1]

    _rate_check(_client_ip(request), byok=byok is not None)

    outcomes = fetch_many(urls)
    ok = [o for o in outcomes if o.article and (o.article.text or "")]
    ok_urls = {o.url for o in ok}
    failed = [
        {"url": o.url, "reason": o.error or "no readable article text found"}
        for o in outcomes
        if o.url not in ok_urls
    ]
    if len(ok) < _MIN_URLS:
        raise HTTPException(
            422,
            {
                "message": "Could not read enough of these pages to compare them.",
                "failed": failed,
            },
        )

    inputs = [
        CompareInput(
            outlet=o.article.outlet,
            title=o.article.title,
            url=o.article.final_url,
            text=o.article.text,
            published_at=o.article.published_at,
        )
        for o in ok
    ]
    try:
        result = compare_sources(inputs, byok=byok)
    except BYOKError as exc:
        raise HTTPException(422, f"Your API key didn't work: {exc}") from None

    lean_by_outlet = {lean.outlet.lower(): lean for lean in result.outlets}
    sources = [
        CompareSourceOut(
            outlet=i.outlet,
            title=i.title,
            url=i.url,
            published_at=i.published_at,
            lean=_lean_out(lean_by_outlet.get(i.outlet.lower())),
        )
        for i in inputs
    ]
    # Any lean objects the model returned under a name that didn't match a source.
    matched = {s.outlet.lower() for s in sources}
    extra = [
        _lean_out(lean) for name, lean in lean_by_outlet.items() if name not in matched
    ]

    out = CompareResultOut(
        relation=result.relation,
        relation_note=result.relation_note,
        shared_facts=result.shared_facts,
        agreements=result.agreements,
        differences=result.differences,
        consensus_slant=result.consensus_slant,
        blind_spots=result.blind_spots,
        takeaway=result.takeaway,
        via=result.via,
        sources=sources,
        unmatched_leans=[e for e in extra if e],
        failed=failed,
    )
    _cache[key] = (time.monotonic(), out)
    return out


def _lean_out(lean) -> OutletLeanOut | None:
    if lean is None:
        return None
    return OutletLeanOut(
        outlet=lean.outlet,
        lean=lean.lean,
        confidence=lean.confidence,
        evidence=lean.evidence,
        loaded_language=lean.loaded_language,
    )
