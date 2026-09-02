from app.ingest.pipeline import _effective_outlets
from app.services.loaded_language import flag_text, score_sentence
from app.services.summarize import SourceItem, _offline


def test_charged_sentence_scores_higher():
    neutral = "The committee met on Tuesday to review the annual budget figures."
    charged = "The disgraceful regime slammed critics in a shocking, brutal crackdown!"
    assert score_sentence(charged) > score_sentence(neutral)


def test_flag_text_returns_charged_sentence():
    text = (
        "Officials confirmed the road will reopen next week. "
        "The so-called reform is a shameful, outrageous scandal that shocked the nation!"
    )
    flags = flag_text(text)
    assert any("scandal" in f.text for f in flags)


def test_offline_summary_flags_differing_casualty_figures():
    items = [
        SourceItem(outlet="A", headline="12 hurt in clash", lead="At least 12 people were hurt."),
        SourceItem(outlet="B", headline="15 injured in unrest", lead="Some 15 people were injured."),
    ]
    result = _offline(items)
    assert result.summary
    assert result.coverage_diff and "injured count varies" in result.coverage_diff
    assert '“12”' in result.coverage_diff and '“15”' in result.coverage_diff


def test_offline_summary_ignores_unlike_figures():
    # different quantities (dead vs rescued vs missing) — not a real disagreement
    items = [
        SourceItem(outlet="A", headline="3 dead in building collapse", lead="Three people died."),
        SourceItem(outlet="B", headline="20 rescued from rubble", lead="Rescuers pulled 20 out."),
    ]
    result = _offline(items)
    assert "varies" not in (result.coverage_diff or "")


def test_offline_summary_always_compares_multi_outlet():
    # near-identical headlines still get a comparison line — it just says so
    items = [
        SourceItem(outlet="A", headline="Dhaka stocks close higher on Sunday", lead="x"),
        SourceItem(outlet="B", headline="Dhaka stocks end the day higher", lead="x"),
        SourceItem(outlet="C", headline="Stocks in Dhaka finish higher", lead="x"),
    ]
    assert _offline(items).coverage_diff


def test_offline_summary_none_for_single_outlet():
    one = [SourceItem(outlet="A", headline="Something happened today", lead="A thing occurred.")]
    assert _offline(one).coverage_diff is None


def test_effective_outlets_collapses_syndicated_copy():
    # two mastheads, one identical headline -> one independent newsroom
    same = "One Nation secures first seat in WA parliament"
    assert _effective_outlets([(1, same), (2, same)]) == 1
    # wire copy on five sites
    assert _effective_outlets([(i, "Fed holds rates steady") for i in range(5)]) == 1
    # a genuine second outlet with its own headline still counts
    assert _effective_outlets([(1, same), (2, same), (3, "One Nation wins historic WA seat")]) == 2
    # one prolific outlet running three angles is still one source
    assert _effective_outlets([(1, "A"), (1, "B"), (1, "C")]) == 1
    # three independent outlets
    assert _effective_outlets([(1, "A"), (2, "B"), (3, "C")]) == 3
