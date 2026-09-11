"""Ad-hoc coverage comparison for the /compare feature.

The user pastes two or more article URLs; `fetch_url` pulls the body text; this
module asks the model to lay the versions side by side and read each outlet's
slant against a neutral baseline (not merely relative to the others — if every
source leans the same way, that is the finding). Falls back to an offline
lexicon read when no model is available.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from app.services.loaded_language import flag_text
from app.services.summarize import BYOKError, call_llm_json, call_llm_json_with

log = logging.getLogger("truenews.compare")

_CONF = ("low", "medium", "high")
_RELATIONS = ("same_event", "related", "unrelated")

_SYSTEM = (
    "You are given, for each outlet, its name and the full text of one article. "
    "Compare how they cover the story. Return STRICT JSON with these keys:\n"
    '{"relation": "same_event|related|unrelated", "relation_note": str, '
    '"shared_facts": str, "agreements": [str], "differences": [str], '
    '"outlets": [{"outlet": str, "lean": str, "confidence": "low|medium|high", '
    '"evidence": [str]}], "consensus_slant": str, "blind_spots": [str], '
    '"takeaway": str}\n\n'
    "FIRST decide 'relation':\n"
    "- 'same_event': all the articles are about the same specific event.\n"
    "- 'related': same broad topic or story, but different events/angles/days.\n"
    "- 'unrelated': the articles are about genuinely different stories.\n"
    "'relation_note': one sentence. For 'unrelated', say plainly that these pieces "
    "are not about the same story and name what each is about — then set agreements, "
    "differences, consensus_slant and blind_spots all empty, give a one-line summary "
    "of each in shared_facts, and still fill 'outlets'. For 'related', note in one "
    "line how they connect.\n\n"
    "shared_facts: 3-6 neutral sentences — the account the articles share (what "
    "happened, who, where, when, key figures). Only facts present in the inputs.\n"
    "agreements: up to 5 short bullets — specific facts or framings most or all share.\n"
    "differences: up to 6 short bullets — each names the outlet(s) and the concrete "
    "divergence: a differing number, a fact one leads with and another omits, a quote "
    "only one carries, sharper or softer wording. No vague bullets. If the outlets are "
    "based in different countries, treat national vantage point as a likely cause of "
    "difference and say so — that is not the same as bias.\n"
    "outlets: one object per outlet. 'lean' is a SHORT plain-language label for how "
    "THIS article is angled, measured against neutral wire-service style — e.g. "
    "'Sympathetic to the protesters', 'Amplifies the government line', 'Sensationalised', "
    "'Downplays the toll'. If the article is a straight, even-handed report, set lean to "
    "'Even-handed' with an empty evidence list. Do NOT grade on a curve: if an article "
    "leans, say so even when the others lean the same way; if none of them lean, label "
    "them all 'Even-handed'. 'confidence' is how strongly the text supports the label. "
    "'evidence' is 1-4 SHORT verbatim quotes from that outlet's own article; empty only "
    "when lean is 'Even-handed'.\n"
    "consensus_slant: if the outlets mostly share a slant or a blind spot, one or two "
    "sentences naming it and what side or angle is missing. Empty string if they are "
    "even-handed or genuinely span the range.\n"
    "blind_spots: up to 4 short bullets — angles, context or voices a reader would need "
    "that NONE of these articles supply. Empty list if the set is well-rounded or "
    "unrelated.\n"
    "takeaway: 1-2 sentences. If every article is even-handed and they agree, just say "
    "the coverage is consistent and a plain summary is enough. Otherwise, what a reader "
    "should keep in mind before trusting any single version.\n\n"
    "Never invent facts, never add outside knowledge beyond what neutral framing would "
    "look like, never declare an outlet simply 'right' or 'wrong'."
)


@dataclass
class CompareInput:
    outlet: str
    title: str
    url: str
    text: str
    published_at: str | None = None


@dataclass
class OutletLean:
    outlet: str
    lean: str
    confidence: str
    evidence: list[str] = field(default_factory=list)
    loaded_language: list[str] = field(default_factory=list)


@dataclass
class CompareResult:
    relation: str  # "same_event" | "related" | "unrelated"
    relation_note: str | None
    shared_facts: str
    agreements: list[str]
    differences: list[str]
    outlets: list[OutletLean]
    consensus_slant: str | None
    blind_spots: list[str]
    takeaway: str
    via: str  # "llm" | "byok" | "offline"


def _clean_list(value: object, limit: int) -> list[str]:
    if not isinstance(value, list):
        return []
    out = [s.strip() for s in value if isinstance(s, str) and s.strip()]
    return out[:limit]


def _as_text(value: object) -> str:
    """The model is asked for a prose string but occasionally hands back a list
    of sentences instead — join those into a paragraph rather than `str()`ing
    the list and leaking Python repr syntax into the page."""
    if isinstance(value, list):
        return " ".join(s.strip() for s in value if isinstance(s, str) and s.strip())
    return str(value or "").strip()


def _user_message(items: list[CompareInput]) -> str:
    return "\n\n".join(
        f"OUTLET: {it.outlet}\nHEADLINE: {it.title}\nARTICLE: {it.text[:3000]}"
        for it in items
    )


def _llm_compare(items: list[CompareInput]) -> CompareResult:
    data = call_llm_json(_SYSTEM, _user_message(items), timeout=50.0)
    return _parse(data, items, via="llm")


def _llm_compare_byok(items: list[CompareInput], provider: str, api_key: str) -> CompareResult:
    """Same prompt, but run against the visitor's own key — never the shared
    pool, and a bad key is a BYOKError (the caller should say so plainly, not
    quietly fall back to a shared-pool result that has nothing to do with it)."""
    data = call_llm_json_with(provider, api_key, _SYSTEM, _user_message(items), timeout=50.0)
    return _parse(data, items, via="byok")


def _parse(data: dict, items: list[CompareInput], *, via: str) -> CompareResult:
    by_name = {it.outlet.lower(): it for it in items}
    leans: list[OutletLean] = []
    for raw in data.get("outlets") or []:
        if not isinstance(raw, dict):
            continue
        name = str(raw.get("outlet") or "").strip()
        if not name:
            continue
        conf = str(raw.get("confidence") or "").lower()
        src = by_name.get(name.lower())
        leans.append(
            OutletLean(
                outlet=name,
                lean=_as_text(raw.get("lean")) or "Unclear",
                confidence=conf if conf in _CONF else "low",
                evidence=_clean_list(raw.get("evidence"), 4),
                loaded_language=[f.text for f in flag_text(src.text)][:4] if src else [],
            )
        )

    summary = _as_text(data.get("shared_facts"))
    if not summary or not leans:
        raise RuntimeError("model response missing required fields")

    relation = str(data.get("relation") or "").strip()
    if relation not in _RELATIONS:
        relation = "related"
    consensus = _as_text(data.get("consensus_slant"))
    return CompareResult(
        relation=relation,
        relation_note=_as_text(data.get("relation_note")) or None,
        shared_facts=summary,
        agreements=_clean_list(data.get("agreements"), 5),
        differences=_clean_list(data.get("differences"), 6),
        outlets=leans,
        consensus_slant=consensus or None,
        blind_spots=_clean_list(data.get("blind_spots"), 4),
        takeaway=_as_text(data.get("takeaway")),
        via=via,
    )


def _offline_compare(items: list[CompareInput]) -> CompareResult:
    """No model: give the extractive shared gist plus a transparent lexicon read
    of each article. Honest about being the fallback."""
    from app.services.summarize import _clean_lead, _first_sentences, _sig_words

    fullest = sorted(items, key=lambda it: len(it.text), reverse=True)
    gist = ""
    for it in fullest[:2]:
        piece = _first_sentences(_clean_lead(it.text), 3)
        if piece and piece[:40] not in gist:
            gist = f"{gist} {piece}".strip()
    gist = gist or (fullest[0].title if fullest else "")

    # Crude same-story check: how much do the headline keywords overlap?
    kw = [_sig_words(it.title) | _sig_words(it.text[:400]) for it in items]
    shared = set.intersection(*kw) if all(kw) else set()
    relation = "related" if len(shared) >= 2 else "unrelated"
    relation_note = (
        None
        if relation == "related"
        else "These pages don't appear to be about the same story — the word-level "
        "check found little in common."
    )

    leans: list[OutletLean] = []
    charged_outlets: list[str] = []
    for it in items:
        flags = [f.text for f in flag_text(it.text)][:4]
        if flags:
            charged_outlets.append(it.outlet)
        leans.append(
            OutletLean(
                outlet=it.outlet,
                lean="Charged language present" if flags else "No lexicon flags",
                confidence="low",
                evidence=[],
                loaded_language=flags,
            )
        )

    consensus = None
    if charged_outlets and len(charged_outlets) == len(items):
        consensus = (
            "Every article here uses emotive or loaded wording — the lexicon check "
            "found charged phrasing in all of them."
        )

    return CompareResult(
        relation=relation,
        relation_note=relation_note,
        shared_facts=gist or "(could not extract a shared summary)",
        agreements=[],
        differences=[],
        outlets=leans,
        consensus_slant=consensus,
        blind_spots=[],
        takeaway=(
            "The comparison model is unavailable right now, so this is a plain "
            "word-level read only. Try again shortly for the full side-by-side."
        ),
        via="offline",
    )


def compare_sources(
    items: list[CompareInput], *, byok: tuple[str, str] | None = None
) -> CompareResult:
    """`byok` = (provider, api_key) when the visitor supplied their own key —
    used for this call only, never logged, never persisted, and kept off the
    shared provider chain entirely."""
    usable = [it for it in items if it.text and len(it.text) > 200]
    if len(usable) < 2:
        raise ValueError("need at least two articles with readable body text")

    if byok:
        provider, api_key = byok
        try:
            return _llm_compare_byok(usable, provider, api_key)
        except BYOKError:
            raise
        except (RuntimeError, KeyError, ValueError, TypeError) as exc:
            raise BYOKError(f"that key didn't return a usable response ({exc})") from exc

    try:
        return _llm_compare(usable)
    except (RuntimeError, KeyError, ValueError, TypeError) as exc:
        log.warning("LLM compare failed (%s); using offline read", exc)
        return _offline_compare(usable)
