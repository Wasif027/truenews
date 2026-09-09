"""Fetch a user-supplied article URL safely, for the /compare feature.

Unlike `extract.py` (which only ever sees URLs from the outlets' own RSS feeds),
this takes URLs pasted by whoever is using the site, so every request is treated
as hostile until proven otherwise:

* scheme must be http/https;
* the host must resolve only to public IP addresses — no loopback, private,
  link-local (cloud metadata at 169.254.169.254), or reserved ranges;
* redirects are followed by hand, re-checking the target each hop;
* the response is size-capped and must look like HTML.

Nothing fetched here is persisted — the body text is handed to the model for the
comparison and then dropped, same as `extract.py`.
"""

from __future__ import annotations

import ipaddress
import logging
import re
import socket
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from dateutil import parser as dateparser

log = logging.getLogger("truenews.fetch_url")

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
_MAX_BYTES = 3_000_000
_MAX_REDIRECTS = 4
_TIMEOUT = httpx.Timeout(9.0)


class UnsafeURL(ValueError):
    """The URL is not something we're willing to fetch server-side."""


@dataclass
class FetchedArticle:
    url: str          # the URL as supplied
    final_url: str     # after redirects
    outlet: str        # site name (og:site_name) or bare host
    title: str
    text: str          # main body, best effort ("" if nothing usable)
    published_at: str | None = None  # ISO 8601 when the page states one


def _resolved_ips(host: str) -> list[ipaddress.IPv4Address | ipaddress.IPv6Address]:
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as exc:
        raise UnsafeURL(f"could not resolve {host!r}") from exc
    return [ipaddress.ip_address(info[4][0]) for info in infos]


def _guard(url: str) -> str:
    """Raise UnsafeURL unless `url` is a public http(s) address. Returns the host."""
    p = urlparse(url)
    if p.scheme not in ("http", "https"):
        raise UnsafeURL("only http and https URLs are supported")
    if not p.hostname:
        raise UnsafeURL("URL has no host")
    if p.port is not None and p.port not in (80, 443):
        raise UnsafeURL("non-standard port")
    for ip in _resolved_ips(p.hostname):
        if (
            ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast
            or ip.is_reserved or ip.is_unspecified
        ):
            raise UnsafeURL("host resolves to a non-public address")
    return p.hostname


def _fetch_html(url: str) -> tuple[bytes, str]:
    """Follow redirects by hand, guarding every hop. Returns (html_bytes, final_url).
    Bytes, not str — BeautifulSoup/lxml sniff the page's own <meta charset>, which
    beats trusting the (often wrong or absent) HTTP charset header."""
    seen = url
    with httpx.Client(
        headers=_UA, timeout=_TIMEOUT, follow_redirects=False, max_redirects=0
    ) as client:
        for _ in range(_MAX_REDIRECTS + 1):
            _guard(seen)
            r = client.get(seen)
            if r.is_redirect:
                nxt = r.headers.get("location", "")
                seen = httpx.URL(seen).join(nxt).human_repr()
                continue
            r.raise_for_status()
            ctype = r.headers.get("content-type", "").lower()
            if "html" not in ctype:
                raise UnsafeURL("that URL is not an HTML page")
            return r.content[:_MAX_BYTES], seen
    raise UnsafeURL("too many redirects")


def _main_text(soup: BeautifulSoup, max_chars: int = 3200) -> str:
    for tag in soup(_DROP):
        tag.decompose()
    root = soup.find("article") or soup.find("main") or soup.body
    if root is None:
        return ""
    paras = [
        t
        for p in root.find_all("p")
        if len(t := p.get_text(" ", strip=True)) > 45 and not _BOILERPLATE.search(t)
    ]
    return re.sub(r"\s+", " ", " ".join(paras)).strip()[:max_chars]


def _meta(soup: BeautifulSoup, *names: str) -> str:
    for name in names:
        tag = soup.find("meta", attrs={"property": name}) or soup.find(
            "meta", attrs={"name": name}
        )
        if tag and tag.get("content", "").strip():
            return tag["content"].strip()
    return ""


def _published(soup: BeautifulSoup) -> str | None:
    raw = _meta(
        soup, "article:published_time", "article:published", "datePublished",
        "publishdate", "pubdate", "date",
    )
    if not raw:
        t = soup.find("time")
        raw = (t.get("datetime") if t else "") or ""
    try:
        return dateparser.parse(raw).isoformat() if raw else None
    except (ValueError, OverflowError, TypeError):
        return None


def fetch_article(url: str) -> FetchedArticle:
    """Fetch and parse one article. Raises UnsafeURL / httpx.HTTPError on failure."""
    html, final_url = _fetch_html(url)
    soup = BeautifulSoup(html, "lxml")  # lxml reads the page's own charset
    host = urlparse(final_url).hostname or ""
    outlet = _meta(soup, "og:site_name", "application-name") or host.removeprefix("www.")
    title = _meta(soup, "og:title") or (
        soup.title.get_text(strip=True) if soup.title else ""
    )
    return FetchedArticle(
        url=url,
        final_url=final_url,
        outlet=outlet,
        title=title,
        text=_main_text(soup),
        published_at=_published(soup),
    )


@dataclass
class FetchOutcome:
    url: str
    article: FetchedArticle | None
    error: str | None


def fetch_many(urls: list[str], *, workers: int = 4) -> list[FetchOutcome]:
    """Fetch several URLs concurrently; never raises — failures come back as
    FetchOutcome.error."""

    def one(u: str) -> FetchOutcome:
        try:
            return FetchOutcome(u, fetch_article(u), None)
        except UnsafeURL as exc:
            return FetchOutcome(u, None, str(exc))
        except httpx.HTTPStatusError as exc:
            return FetchOutcome(u, None, f"the site returned {exc.response.status_code}")
        except httpx.HTTPError:
            return FetchOutcome(u, None, "could not be reached")

    with ThreadPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(one, urls))
