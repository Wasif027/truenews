"""Best-effort main-text extraction for the coverage comparison.

We fetch each outlet's article page at summarise time, pull the body text, hand
it to the model, and throw it away. Nothing here is persisted — only the model's
comparison is stored. Any failure (403, timeout, paywall, JS-only page) returns
an empty string and the caller falls back to the RSS opening paragraph.
"""

from __future__ import annotations

import logging
import re
from concurrent.futures import ThreadPoolExecutor

import httpx
from bs4 import BeautifulSoup

log = logging.getLogger("truenews.extract")

_UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}
_DROP = (
    "script", "style", "nav", "aside", "figure", "figcaption", "form", "header",
    "footer", "noscript", "iframe", "button", "svg",
)
_BOILERPLATE = re.compile(
    r"also read|read more|read also|subscribe|sign up|follow us|advertisement|"
    r"related (news|stories|articles)|©|all rights reserved",
    re.IGNORECASE,
)

# Per-process cache — a re-summarise in the same run won't re-fetch. Never written
# to disk or the database.
_cache: dict[str, str] = {}


def _extract(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(_DROP):
        tag.decompose()
    root = soup.find("article") or soup.find("main") or soup.body
    if root is None:
        return ""
    paras: list[str] = []
    for p in root.find_all("p"):
        t = p.get_text(" ", strip=True)
        if len(t) > 45 and not _BOILERPLATE.search(t):
            paras.append(t)
    return re.sub(r"\s+", " ", " ".join(paras)).strip()


def article_text(url: str, *, max_chars: int = 2600, timeout: float = 8.0) -> str:
    if url in _cache:
        return _cache[url]
    body = ""
    try:
        r = httpx.get(
            url, headers=_UA, timeout=httpx.Timeout(timeout), follow_redirects=True
        )
        if r.status_code == 200 and "html" in r.headers.get("content-type", "").lower():
            body = _extract(r.text)[:max_chars]
    except (httpx.HTTPError, ValueError):
        body = ""
    _cache[url] = body
    return body


def prefetch(urls: list[str], *, workers: int = 8) -> None:
    """Warm the cache for a batch of URLs concurrently."""
    todo = [u for u in dict.fromkeys(urls) if u not in _cache]
    if not todo:
        return
    with ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(article_text, todo))
    got = sum(1 for u in todo if _cache.get(u))
    log.info("fetched article text for %d/%d sources", got, len(todo))
