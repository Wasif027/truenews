from __future__ import annotations

import json
import logging
import re
import time
from collections import Counter
from dataclasses import dataclass

import httpx

from app.config import get_settings

log = logging.getLogger("truenews.summarize")

_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")
_NUM_TOKEN = re.compile(r"\d[\d,]*(?:\.\d+)?")
# Words next to a number that say what it counts. Grouped so we only compare
# like with like — "12 dead" vs "15 dead" is worth flagging, "12 dead" vs
# "15 rescued" is not.
_FIG_KINDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("death toll", ("dead", "killed", "toll", "die", "died", "dies", "fatalit",
                    "bodies", "perish", "lives lost")),
    ("injured count", ("injured", "wounded", "hurt")),
    ("number missing", ("missing", "unaccounted")),
)
# Words right before a number that mean it is NOT a casualty figure.
_NUM_ANTI = ("day", "vol", "part", "phase", "week", "round", "match", "group of",
             "aged", "age", "chapter", "no.")
_CLAUSE_END = re.compile(r"[,;:–—]")

# Navigational cruft that RSS leads often tack on; everything from here is dropped.
_LEAD_JUNK = re.compile(
    r"\b(?:also\s*read|read\s*more|read\s*also|more\s*to\s*read|story\s*continues|"
    r"advertisement|click\s*here|watch\s*:|watch\s*video|follow\s*us|subscribe|"
    r"district-?wise\s*toll)\b.*$",
    re.IGNORECASE | re.DOTALL,
)

# Verbs/nouns that editorialise — a headline using one is taking an angle.
_CHARGED = (
    "slams", "blasts", "rips", "lashes", "condemns", "fumes", "defiant", "backlash",
    "outrage", "fury", "chaos", "scandal", "shock", "slammed", "blasted", "rages",
    "meltdown", "humiliation", "triumph", "fiasco", "botched", "debacle", "crushes",
    "thrashes", "thrash", "hammers", "demolish", "stun", "stuns",
)
# Softer attribution/stance verbs worth surfacing when only some outlets use them.
_STANCE = (
    "urges", "claims", "insists", "denies", "admits", "accuses", "blames", "defends",
    "refuses", "rejects", "demands", "alleges", "concedes", "downplays", "warns", "vows",
)

_WORD = re.compile(r"[A-Za-z][A-Za-z'’-]{2,}")
_HL_STOP = frozenset({
    "the", "and", "for", "was", "were", "with", "from", "after", "before", "over", "into",
    "out", "off", "amid", "says", "say", "said", "new", "his", "her", "their", "its",
    "that", "this", "these", "those", "they", "you", "not", "more", "most", "than", "then",
    "will", "would", "can", "could", "may", "might", "but", "about", "against", "between",
    "near", "two", "three", "four", "five", "who", "what", "when", "where", "why", "how",
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
    "january", "february", "march", "april", "june", "july", "august", "september",
    "october", "november", "december", "today", "yesterday", "tomorrow", "week", "year",
    "latest", "update", "updates", "live", "breaking", "watch", "video",
})


def _norm_word(w: str) -> str:
    w = w.strip("'’\"-").lower()
    return w[:-2] if w.endswith(("'s", "’s")) else w
# Verbs so common in headlines that "only some outlets use it" means nothing.
_GENERIC_HL = frozenset({
    "report", "reports", "reported", "say", "says", "said", "tell", "told", "confirm",
    "confirms", "confirmed", "announce", "announces", "announced", "reveal", "reveals",
    "revealed", "get", "gets", "got", "win", "wins", "won", "lose", "loses", "set", "sets",
    "make", "makes", "made", "take", "takes", "took", "hold", "holds", "held", "call",
    "calls", "called", "face", "faces", "give", "gives", "gave", "show", "shows", "plan",
    "plans", "move", "moves", "seek", "seeks", "govt", "amid",
})

_NUM_WORDS = {2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven",
              8: "eight", 9: "nine"}


def _num_word(n: int) -> str:
    return _NUM_WORDS.get(n, str(n))


def _sig_words(headline: str) -> set[str]:
    out: set[str] = set()
    for w in _WORD.findall(headline):
        n = _norm_word(w)
        if len(n) >= 3 and n not in _HL_STOP and n not in _GENERIC_HL:
            out.add(n)
    return out


def _proper_nouns(items: list[SourceItem]) -> set[str]:
    """Words that read as names / places / organisations: capitalised in most of
    the headlines that use them (ignoring the odd sentence-initial capital)."""
    seen: Counter[str] = Counter()
    capped: Counter[str] = Counter()
    for it in items:
        for i, w in enumerate(_WORD.findall(it.headline)):
            lw = _norm_word(w)
            if len(lw) < 3 or lw in _HL_STOP or lw in _GENERIC_HL:
                continue
            seen[lw] += 1
            if w[0].isupper() and (i > 0 or w != w.upper()):
                capped[lw] += 1
    return {w for w, n in seen.items() if capped[w] >= max(1, n * 0.6)}


@dataclass
class SourceItem:
    outlet: str
    headline: str
    lead: str
    body: str = ""  # full article text when available (LLM path only, never stored)


@dataclass
class SummaryResult:
    summary: str
    coverage_diff: str | None
    coverage_detail: str | None = None
    categories: list[str] | None = None  # 1-2 slugs from _CATEGORY_SLUGS, best first
    via: str = "offline"  # "llm" or "offline" — the caller retries "offline" later


_CATEGORY_SLUGS = (
    "politics", "business", "international", "sports", "health",
    "technology", "entertainment", "general",
)

_SYSTEM = (
    "You compare how different news outlets cover the same event. For each outlet "
    "you are given its headline and either its full article text or, when that "
    "could not be fetched, its opening paragraph. Return STRICT JSON: "
    '{"summary": str, "coverage_diff": str, "coverage_detail": str, "categories": [str]}. '
    "summary: 4-6 neutral sentences covering what happened, who is involved, where and when, "
    "and any figures or consequences reported. Use only facts present in the inputs. "
    "coverage_diff: 1-3 sentences, the single biggest way the coverage differs - framing, a "
    "differing number, or a fact one outlet leads with and others omit. Empty string if uniform. "
    "coverage_detail: 4-7 sentences walking through how the individual outlets handled it, "
    "naming them - who led with what, who emphasised or buried which angle, who included a "
    "detail or quote the others omitted, whose wording is sharpest. Prefer differences that "
    "show up in the article body, not just the headline. Group outlets that did the same "
    "thing. Empty string only if the coverage is genuinely indistinguishable. "
    "categories: 1 or 2 topic slugs for this story, most relevant first, chosen ONLY from: "
    "politics, business, international, sports, health, technology, entertainment, general. "
    '"international" means a foreign country or global affairs from the reader\'s perspective - '
    "add it only when there is a genuine foreign angle, never for a purely domestic story. "
    '"general" is the catch-all for crime, courts, accidents, disasters, weather and civic life. '
    "Give a second slug only when a second topic is clearly present. "
    "Never speculate, never add outside knowledge, never state which outlet is right."
)


def _clean_lead(text: str) -> str:
    """Tidy an RSS lead: collapse whitespace, repair missing spaces after a
    full stop ("disaster.Bodies" -> "disaster. Bodies"), drop trailing
    "Also read: ..." navigation."""
    t = re.sub(r"\s+", " ", text or "").strip()
    t = re.sub(r"([a-z0-9)\]\"'”’])([.!?])([A-Z\"'“‘(])", r"\1\2 \3", t)
    t = re.sub(r"(\d)([A-Z][a-z])", r"\1 \2", t)  # "2026Ramon" -> "2026 Ramon"
    t = _LEAD_JUNK.sub("", t).strip()
    return t


def _lead_quality(lead: str) -> tuple[int, int]:
    """Sort key (worse first): leads with glued tokens or a very long unbroken
    run look like scraper artefacts — fall back to them only if nothing cleaner."""
    messy = bool(re.search(r"\d{5,}|[a-z]{18,}|\S{28,}", lead))
    return (1 if messy else 0, -len(lead))


def _first_sentences(text: str, n: int) -> str:
    parts = _SENT_SPLIT.split(text.strip())
    return " ".join(parts[:n]).strip()


def _trim(text: str, limit: int) -> str:
    """Cut to <= limit chars, preferably on a sentence boundary."""
    if len(text) <= limit:
        return text
    cut = text[:limit]
    dot = max(cut.rfind(". "), cut.rfind("! "), cut.rfind("? "))
    return cut[: dot + 1] if dot > limit * 0.55 else cut.rstrip(" ,;:") + "…"


def _nearest(text: str, words: tuple[str, ...]) -> int:
    """Character distance to the closest of `words` in `text`, or 1e9 if none."""
    hits = [text.find(w) for w in words if w in text]
    return min(hits) if hits else 10**9


def _casualty_figure(headline: str) -> tuple[str, str]:
    """(number, kind) for the first casualty figure a headline states —
    e.g. "toll rises to 781" -> ("781", "death toll"), "15 injured" ->
    ("15", "injured count"). ("", "") when no number sits next to a
    casualty word. A cue right before the number ("toll hits N") wins; a cue
    after it only counts within the same clause ("N killed", not "N, X hurt")."""
    low = headline.lower()
    for m in _NUM_TOKEN.finditer(headline):
        tok = m.group(0).strip(" ,.;:")
        if not tok.replace(",", "").isdigit():
            continue
        just_before = low[max(0, m.start() - 9) : m.start()].strip(" :-")
        if any(just_before.endswith(w) for w in _NUM_ANTI):
            continue
        back = low[max(0, m.start() - 26) : m.start()][::-1]
        tail = low[m.end() : m.end() + 16]
        stop = _CLAUSE_END.search(tail)
        fwd = tail[: stop.start()] if stop else tail
        for kind, words in _FIG_KINDS:
            d_back = _nearest(back, tuple(w[::-1] for w in words))
            d_fwd = _nearest(fwd, words)
            if d_back <= 24 or d_fwd <= 12:
                return tok, kind
    return "", ""


def _short_outlet(name: str) -> str:
    """Trim "(English)" / "Online" tails so the diff reads cleanly."""
    return re.sub(
        r"\s*\((?:english|online|web|digital)\)\s*$", "", name, flags=re.IGNORECASE
    ).strip()


def _coverage_notes(items: list[SourceItem]) -> list[str]:
    """Concrete, source-grounded notes on how the headlines differ. Headline-only
    (leads are too noisy to compare word-for-word). Returns [] rather than
    anything vague."""
    if len(items) < 2:
        return []
    notes: list[str] = []
    haystacks = {_short_outlet(it.outlet): f" {it.headline.lower()} " for it in items}

    # 1. Do the headlines disagree on a casualty figure of the same kind?
    by_kind: dict[str, dict[str, str]] = {}
    for it in items:
        num, kind = _casualty_figure(it.headline)
        if kind:
            by_kind.setdefault(kind, {})[_short_outlet(it.outlet)] = num
    for kind, figs in by_kind.items():
        if len(figs) >= 2 and len(set(figs.values())) > 1:
            rendered = "; ".join(f"{o} says “{n}”" for o, n in list(figs.items())[:3])
            notes.append(f"The reported {kind} varies — {rendered}.")
            break

    # 2. Charged vs plain framing.
    charged = [o for o, h in haystacks.items() if any(w in h for w in _CHARGED)]
    if charged and len(charged) < len(haystacks):
        plain = [o for o in haystacks if o not in charged]
        notes.append(
            f"{_and_list(charged)} {_verb(charged, 'use', 'uses')} sharper wording, while "
            f"{_and_list(plain)} {_verb(plain, 'keep', 'keeps')} it plain."
        )

    # 3. A stance verb only some outlets use (urges / claims / denies ...).
    for verb in _STANCE:
        users = [o for o, h in haystacks.items() if f" {verb} " in h]
        if users and len(users) < len(haystacks):
            notes.append(
                f"{_and_list(users)} {_verb(users, 'cast', 'casts')} it as someone "
                f"“{verb}” something; the others report it flat."
            )
            break

    # 4. A concrete detail (name, place, org) some headlines carry and others drop.
    term = _distinctive_term(items)
    if term:
        notes.append(term)

    return notes


def _distinctive_term(items: list[SourceItem]) -> str:
    n = len(items)
    if n < 2:
        return ""
    per = {_short_outlet(it.outlet): _sig_words(it.headline) for it in items}
    proper = _proper_nouns(items)
    freq: Counter[str] = Counter()
    for words in per.values():
        freq.update(words)
    # Only a proper noun (a name / place / org some headlines print and others
    # don't) is a reliable "different detail" signal. Ordinary word choice is
    # too noisy — that case falls through to the alignment note.
    cands = [w for w in proper if 1 <= freq[w] < n and len(w) >= 3]
    if not cands:
        return ""

    term = max(cands, key=lambda w: (-freq[w], len(w)))  # rarest, then longest
    have = [o for o, ws in per.items() if term in ws]
    lack = [o for o in per if o not in have]
    disp = " ".join(p.capitalize() for p in re.split(r"[-'’]", term))
    if len(have) <= len(lack):
        return f"Only {_and_list(have)} {_verb(have, 'mention', 'mentions')} “{disp}”."
    return (
        f"{_and_list(lack)} {_verb(lack, 'leave out', 'leaves out')} “{disp}”, "
        f"which the other headlines keep."
    )


def _alignment_note(items: list[SourceItem]) -> str:
    """Always returns something for 2+ outlets: what the coverage has in common."""
    n = len(items)
    freq: Counter[str] = Counter()
    for it in items:
        freq.update(_sig_words(it.headline))
    lead_in = "Both outlets" if n == 2 else f"All {_num_word(n)} outlets"
    shared = [w for w, c in freq.most_common() if c >= max(2, (n + 1) // 2)]
    if shared:
        first = [w.lower() for w in _WORD.findall(items[0].headline)]
        shared.sort(key=lambda w: first.index(w) if w in first else 99)
        gist = " ".join(shared[:4])
        return (
            f"{lead_in} lead with the same development ({gist}); "
            f"the headlines differ only in wording."
        )
    return f"{lead_in} report the same event with closely matched wording."


def _verb(subjects: list[str], plural: str, singular: str) -> str:
    return singular if len(subjects) == 1 else plural


def _and_list(names: list[str]) -> str:
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return f"{', '.join(names[:-1])} and {names[-1]}"


def _offline(items: list[SourceItem]) -> SummaryResult:
    # Stitch the openings from the two fullest sources for a bit more detail.
    leads = sorted(
        (c for c in (_clean_lead(it.lead) for it in items if it.lead) if c),
        key=_lead_quality,
    )
    if leads:
        summary = _first_sentences(leads[0], 4)
        if len(leads) > 1 and len(summary) < 340:
            extra = _first_sentences(leads[1], 2)
            if extra and extra[:40] not in summary:
                summary = f"{summary} {extra}"
    else:
        summary = items[0].headline if items else ""
    summary = _trim(summary, 640)

    # Always give a multi-outlet story a comparison line. Prefer a concrete
    # difference; fall back to stating what the coverage has in common. The
    # richer per-outlet breakdown (coverage_detail) stays an LLM job.
    notes = _coverage_notes(items)
    if not notes and len(items) >= 2:
        notes = [_alignment_note(items)]
    diff = notes[0] if notes else None
    return SummaryResult(
        summary=summary or "(summary unavailable)",
        coverage_diff=diff,
        coverage_detail=None,
    )


# Free tiers rate-limit hard (per-minute request/token limits + per-day caps).
# ~5s between calls keeps us comfortably under a 15-requests/minute free tier;
# roll straight to the next model / provider on any limit rather than backing off.
_MIN_GAP_S = 5.0
_last_call = 0.0
# When everything is per-minute-limited, stop trying for a bit — otherwise a run
# of clusters each grinds through the full gauntlet and holds the DB transaction
# open long enough for Neon to drop it. Offline covers these; next run retries.
_cooldown_until = 0.0

_QUOTA_HINTS = ("per day", "quota", "resource_exhausted", "daily limit", "tokens per day")


def _models() -> list[tuple[str, str, str]]:
    """(base_url, api_key, model) — one row per model across all providers."""
    return [
        (base.rstrip("/"), key, m.strip())
        for base, key, model_csv in get_settings().llm_providers
        for m in model_csv.split(",")
        if m.strip()
    ]


def _quota_limit(resp: httpx.Response) -> bool:
    return resp.status_code == 429 and any(h in resp.text.lower() for h in _QUOTA_HINTS)


def _llm(items: list[SourceItem]) -> SummaryResult:
    global _last_call, _cooldown_until
    if time.monotonic() < _cooldown_until:
        raise RuntimeError("LLM cooling down after rate limits")
    body = "\n\n".join(
        f"OUTLET: {it.outlet}\nHEADLINE: {it.headline}\n"
        + (f"ARTICLE: {it.body[:700]}" if it.body else f"OPENING: {it.lead}")
        for it in items[:4]
    )

    resp: httpx.Response | None = None
    rows = _models()
    limited = 0  # rows that came back rate/quota limited
    quota_hit = False
    for base, key, model in rows:
        payload = {
            "model": model,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": body},
            ],
        }
        for attempt in range(2):
            gap = time.monotonic() - _last_call
            if gap < _MIN_GAP_S:
                time.sleep(_MIN_GAP_S - gap)
            resp = httpx.post(
                f"{base}/chat/completions",
                headers={"Authorization": f"Bearer {key}"},
                json=payload,
                timeout=httpx.Timeout(90.0),
            )
            _last_call = time.monotonic()
            if resp.status_code == 429:
                limited += 1
                if _quota_limit(resp):
                    quota_hit = True
                elif attempt == 0:  # per-minute: one short wait, then move on
                    time.sleep(min(6.0, float(resp.headers.get("retry-after") or 4)))
                    continue
            break

        if resp.status_code == 200:
            try:
                data = json.loads(resp.json()["choices"][0]["message"]["content"])
                summary = data["summary"].strip()
            except (KeyError, ValueError):
                summary = ""
            if summary:
                diff = (data.get("coverage_diff") or "").strip()
                detail = (data.get("coverage_detail") or "").strip()
                cats = [
                    c for c in (data.get("categories") or [])
                    if isinstance(c, str) and c in _CATEGORY_SLUGS
                ][:2]
                return SummaryResult(summary, diff or None, detail or None, cats or None, "llm")

        # quota cap, a 400 "failed to generate JSON", a 5xx, garbage output —
        # all recoverable by trying the next model / provider.
        log.info("%s (%s) unusable (%s); trying next", model, base, resp.status_code)

    # Every provider was rate/quota limited for this call — the next cluster will
    # be no different. Back off so a run doesn't crawl through the whole gauntlet
    # per story (and hold the DB transaction open). Longer for a daily cap.
    if rows and limited >= len(rows):
        _cooldown_until = time.monotonic() + (900 if quota_hit else 60)
        log.info("all providers limited; pausing LLM for %ds", 900 if quota_hit else 60)
    if resp is not None:
        resp.raise_for_status()  # everything failed -> surface the last error
    raise RuntimeError("no LLM provider configured")


def summarise(items: list[SourceItem], *, use_llm: bool = True) -> SummaryResult:
    """Summary + coverage comparison for one story. Uses the model when a key is
    configured and `use_llm` is set; otherwise (or on any model failure) returns
    the offline extractive version."""
    if not items:
        return SummaryResult(summary="", coverage_diff=None)
    if not (use_llm and get_settings().llm_providers):
        return _offline(items)
    try:
        return _llm(items)
    except (httpx.HTTPError, KeyError, ValueError, json.JSONDecodeError, RuntimeError) as exc:
        log.warning("LLM summarise failed (%s); using offline fallback", exc)
        return _offline(items)
