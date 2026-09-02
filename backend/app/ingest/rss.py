from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import UTC, datetime

import feedparser
import httpx
from bs4 import BeautifulSoup
from dateutil import parser as dateparser

from app.ingest.sources import SourceConfig

log = logging.getLogger("truenews.rss")

# Some outlets 403 a bot-looking UA; a browser-ish one gets through more feeds.
_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36 TrueNewsBot/0.1"
)
_TIMEOUT = httpx.Timeout(20.0)


@dataclass
class RawArticle:
    url: str
    headline: str
    byline: str | None
    lead_text: str
    published_at: datetime
    # Placeholder until _embed_new runs the real categoriser a moment later.
    category: str = "general"


def _clean_html(raw: str) -> str:
    text = BeautifulSoup(raw or "", "lxml").get_text(" ", strip=True)
    return re.sub(r"\s+", " ", text).strip()


def _parse_date(entry) -> datetime:
    for key in ("published", "updated", "created"):
        val = entry.get(key)
        if val:
            try:
                dt = dateparser.parse(val)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=UTC)
                return dt.astimezone(UTC)
            except (ValueError, OverflowError):
                continue
    if entry.get("published_parsed"):
        return datetime(*entry.published_parsed[:6], tzinfo=UTC)
    return datetime.now(UTC)


def _fetch_one(slug: str, feed_url: str) -> list[RawArticle]:
    try:
        resp = httpx.get(
            feed_url,
            headers={"User-Agent": _UA, "Accept": "application/rss+xml, application/xml, text/xml"},
            timeout=_TIMEOUT,
            follow_redirects=True,
        )
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        log.warning("fetch failed for %s (%s): %s", slug, feed_url, exc)
        return []

    parsed = feedparser.parse(resp.content)
    if parsed.bozo and not parsed.entries:
        log.warning("unparseable feed for %s (%s): %s", slug, feed_url, parsed.get("bozo_exception"))
        return []

    out: list[RawArticle] = []
    for entry in parsed.entries:
        url = (entry.get("link") or "").strip()
        headline = _clean_html(entry.get("title") or "")
        if not url or not headline:
            continue
        summary = entry.get("summary") or entry.get("description") or ""
        if not summary and entry.get("content"):
            summary = entry["content"][0].get("value", "")
        lead = _clean_html(summary)[:1200]
        byline = (entry.get("author") or "").strip() or None
        out.append(
            RawArticle(
                url=url,
                headline=headline,
                byline=byline,
                lead_text=lead,
                published_at=_parse_date(entry),
            )
        )
    return out


def fetch_feed(source: SourceConfig) -> list[RawArticle]:
    """Fetch every configured feed for an outlet, merge, de-duplicate by URL.
    Never raises for network/parse issues — logs and skips the bad feed."""
    seen: set[str] = set()
    merged: list[RawArticle] = []
    for feed_url in source.feeds:
        for art in _fetch_one(source.slug, feed_url):
            if art.url in seen:
                continue
            seen.add(art.url)
            merged.append(art)
    log.info("fetched %d items from %s (%d feeds)", len(merged), source.slug, len(source.feeds))
    return merged
