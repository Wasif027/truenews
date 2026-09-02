"""Loaded-language flagging.

v1 is a transparent lexicon scorer: charged/emotive terms + intensifiers +
punctuation. It is intentionally simple so the /how-it-works page can describe it
exactly. Swap `score_sentence` for a BABE-trained classifier
(e.g. a RoBERTa fine-tuned on the media-bias-group BABE dataset) when you want
better recall - the interface stays the same.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")

_CHARGED = {
    "slammed", "blasted", "lashed", "outrage", "outrageous", "shocking", "shameful",
    "disgraceful", "chaos", "crisis", "catastrophe", "disaster", "scandal", "regime",
    "crackdown", "propaganda", "so-called", "claimed", "alleged", "admitted", "refused",
    "desperate", "brutal", "draconian", "radical", "extremist", "mob", "thugs", "puppet",
    "landmark", "historic", "unprecedented", "stunning", "massive", "devastating",
}
_INTENSIFIERS = {"very", "extremely", "utterly", "completely", "totally", "absolutely",
                 "wildly", "deeply", "hugely"}


@dataclass
class Flag:
    text: str
    score: float


def score_sentence(sentence: str) -> float:
    words = re.findall(r"[a-z'-]+", sentence.lower())
    if not words:
        return 0.0
    charged = sum(1 for w in words if w in _CHARGED)
    intens = sum(1 for w in words if w in _INTENSIFIERS)
    bang = sentence.count("!")
    scare_quotes = len(re.findall(r"[\"'].{1,30}?[\"']", sentence))
    raw = 1.6 * charged + 0.8 * intens + 1.0 * bang + 0.5 * scare_quotes
    return min(1.0, raw / max(6.0, len(words) / 4))


def flag_text(text: str, threshold: float = 0.34) -> list[Flag]:
    flags: list[Flag] = []
    for sent in _SENT_SPLIT.split(text.strip()):
        sent = sent.strip()
        if len(sent) < 20:
            continue
        s = score_sentence(sent)
        if s >= threshold:
            flags.append(Flag(text=sent, score=round(s, 3)))
    return flags
