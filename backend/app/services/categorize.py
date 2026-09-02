"""Zero-shot story categorization.

Embed a one-line description of each category once, then score the article's
headline embedding (the same bge-small vector already computed for clustering)
against all of them. A story gets a primary category and, when a second topic is
genuinely close, a secondary one. "international" is treated as a modifier: it is
only attached when the story actually has a foreign angle, and a purely domestic
story keeps its real topic instead.

`categorize()` returns a list of 1 or 2 category slugs, most prominent first.
"""

from __future__ import annotations

from functools import lru_cache

import numpy as np

from app.services.embeddings import embed_texts

_PROMPTS: dict[str, str] = {
    "sports": (
        "A sports report about a match, game, final, tournament, series, score, "
        "league, team, player, coach, wicket, goal, or medal, in cricket, "
        "football, tennis or another sport."
    ),
    "business": (
        "A business or economy story about markets, stocks, shares, a company, a "
        "bank, trade, exports, tariffs, inflation, the budget, earnings, "
        "layoffs or the wider economy."
    ),
    "politics": (
        "A politics story about an election, the government, parliament, a "
        "political party, a minister or political leader, a policy, a bill, a "
        "coalition or a political protest."
    ),
    "international": (
        "A story about a foreign country or global affairs: a war, a foreign "
        "election, diplomacy, a summit, a treaty, or a disaster, accident or "
        "attack that happened abroad."
    ),
    "technology": (
        "A technology story about software, an app, artificial intelligence, a "
        "phone or gadget, the internet, a chip, a data breach or cyberattack, or "
        "a rocket or satellite launch."
    ),
    "entertainment": (
        "An entertainment story about a film or movie, music, an album, a "
        "concert, television or streaming, a celebrity, or an awards show."
    ),
    "health": (
        "A health or medicine story about a disease outbreak, a hospital, a "
        "vaccine, medical research, mental health, drugs, or public health."
    ),
    "general": (
        "A hard-news story about an accident, a fire, a road or boat crash, a "
        "crime, a shooting, a court case, the weather, a rescue, an obituary, or "
        "civic life."
    ),
    # "promotions" is deliberately keyword-only (see _OVERRIDES) — the embedding
    # comparison kept mistaking "tariff order on goods" and similar for an ad.
}
_KEYS: list[str] = list(_PROMPTS)
_INTL = _KEYS.index("international")

# A secondary category is added only when its score is within this fraction of
# the primary's and clears the absolute floor. Tuned on real multi-country feeds.
_SECONDARY_REL = 0.95
_SECONDARY_MIN = 0.42

_OVERRIDES: dict[str, tuple[str, ...]] = {
    "promotions": ("sponsored:", "sponsored |", "advertorial", "paid partnership",
                   "sponsored content", "sponsored feature", "promoted content",
                   "advertisement feature", "brandconnect"),
}

# Crime / courts / policing. These stories keep landing in technology or business
# because of incidental words ("electronic devices", "fraud", "ICT" = the
# International Crimes Tribunal). When one of these is present the story is
# "general" unless it is really political or foreign.
_CRIME = (
    "murder", "murdered", "homicide", "rape", "raped", "gang-rape", "assault",
    "arrested", "arrest", "detained", "charged with", "chargesheet", "charge sheet",
    "sentenced", "verdict", "acquitted", "convicted", "conviction", "prosecutor",
    "on trial", "court case", "tribunal", "in custody", "granted bail", "denied bail",
    "stabbed", "shot dead", "gunman", "gunmen", "kidnap", "abduct", "extortion",
    "fraud case", "ponzi", "embezzl", "money laundering", "smuggl", "trafficking",
    "enforced disappearance", "extrajudicial", "mugging", "mugged", "robbery", "burglary",
    "looted", "snatching", "lynched", "assaulted", "beaten to death", "hacked to death",
)

# Edition code -> words that mean "this is domestic".
_OWN: dict[str, tuple[str, ...]] = {
    "bd": ("bangladesh", "bangladeshi", "dhaka", "chattogram", "chittagong", "sylhet",
           "rajshahi", "khulna", "barishal", "rangpur", "mymensingh", "cox's bazar",
           "padma", "jamuna", "awami", "bnp", "jatiya", "hasina", "yunus"),
    "in": ("india", "indian", "delhi", "mumbai", "bengaluru", "kolkata", "chennai",
           "hyderabad", "modi", "bjp", "congress", "lok sabha", "rajya sabha", "rbi",
           "supreme court of india", "kerala", "gujarat", "punjab", "bihar", "assam"),
    "pk": ("pakistan", "pakistani", "karachi", "lahore", "islamabad", "peshawar",
           "punjab", "sindh", "imran khan", "pti", "pml", "rawalpindi"),
    "ng": ("nigeria", "nigerian", "lagos", "abuja", "tinubu", "kano", "ibadan"),
    "ph": ("philippines", "filipino", "philippine", "manila", "cebu", "marcos",
           "davao", "quezon city"),
    "uk": ("britain", "british", "uk ", "england", "scotland", "wales", "london",
           "nhs", "westminster", "downing street", "labour", "tory", "tories", "starmer"),
    "us": ("u.s.", "us ", "america", "american", "washington", "new york", "california",
           "trump", "biden", "congress", "white house", "florida", "texas"),
    "au": ("australia", "australian", "sydney", "melbourne", "canberra", "albanese",
           "queensland", "perth"),
    "ie": ("ireland", "irish", "dublin", "cork", "dail", "taoiseach", "galway"),
    "sg": ("singapore", "singaporean", "hdb", "mrt"),
    "my": ("malaysia", "malaysian", "kuala lumpur", "anwar", "putrajaya", "johor"),
    "ca": ("canada", "canadian", "ottawa", "toronto", "ontario", "quebec", "alberta",
           "vancouver", "montreal", "carney", "poilievre", "trudeau"),
    "nz": ("new zealand", "zealand", "kiwi", "auckland", "wellington", "christchurch",
           "aotearoa", "luxon", "hipkins", "maori"),
    "za": ("south africa", "south african", "johannesburg", "pretoria", "cape town",
           "durban", "ramaphosa", " anc ", " eff ", "zuma", "soweto"),
    "ke": ("kenya", "kenyan", "nairobi", "mombasa", "ruto", "odinga", "nakuru", "kisumu"),
    "gh": ("ghana", "ghanaian", "accra", "kumasi", "mahama", "akufo-addo", "cedi",
           " ndc ", " npp "),
    "ug": ("uganda", "ugandan", "kampala", "entebbe", "museveni", "besigye", "bobi wine"),
    "zw": ("zimbabwe", "zimbabwean", "harare", "bulawayo", "mnangagwa", "zanu-pf", "chamisa"),
    "jp": ("japan", "japanese", "tokyo", "osaka", "kyoto", "ishiba", "kishida", " ldp "),
    "lk": ("sri lanka", "sri lankan", "colombo", "kandy", "jaffna", "dissanayake",
           "rajapaksa", "wickremesinghe"),
    "np": ("nepal", "nepali", "nepalese", "kathmandu", "pokhara", " oli ", "deuba",
           "prachanda", "everest"),
    "jm": ("jamaica", "jamaican", "kingston", "montego bay", "holness", " jlp ", " pnp "),
}

# War / attack / disaster words. With one of these plus a foreign place, a story
# is international whatever the embedding picked.
_CONFLICT = (
    "airstrike", "air strike", "air strikes", "strikes", "struck", "shelling",
    "missile", "drone strike", "troops", "ceasefire", "militant", "insurgent",
    "offensive", "invasion", "genocide", "war crimes", " war ", "at war", "killed",
    "death toll", "casualties", "bombing", "blast", "attack", "earthquake",
    "landslide", "typhoon", "hurricane", "wildfire", "famine", "coup", "annex",
)

# "X wins / receives an award" is not a sports story unless it is clearly sport.
_AWARD = ("award", " prize", "laureate", "felicitat", "honoured with", "honored with")
_SPORTS_CTX = (
    "olympic", "medal", "world cup", "championship", "grand prix", "tournament",
    "league", "wicket", " goal", "knockout", "icc", "fifa", "uefa", "nba", "batter",
    "batsman", "bowler", "all-rounder", " test ", " odi", " t20", "grand slam",
    "ballon d'or", "player of the", "coach of the", "golden boot", "mvp", "cricket",
    "football", "tennis", "athletics", "sprint", "marathon", "formula 1", "f1 ",
)

# Unambiguous sport signals — a story with one of these is sport whatever the
# embedding thought (football transfers read as "business", sports politics as
# "politics").
_SPORT_STRONG = (
    "fifa", "uefa", " ioc ", "premier league", "la liga", "serie a", "bundesliga",
    "champions league", "europa league", "world cup", "asia cup", "champions trophy",
    "transfer window", "transfer fee", "signs for", "loan move", "test match",
    "one-day international", " odi ", " t20 ", "t20i", "innings", "wickets", "batting",
    "bowling", "half-century", "century stand", "grand slam", "wimbledon", "us open",
    "french open", "australian open", "formula 1", "motogp", "olympics", "asian games",
    "commonwealth games", "ballon", "golden boot", "man of the match", "clean sheet",
)
_ENT_STRONG = (
    "box office", "box-office", "film review", "movie review", "trailer released",
    "teaser out", "first look", "new album", "new single", "music video", "world tour",
    "concert tour", "netflix series", "prime video", "web series", "streaming on",
    "bollywood", "hollywood", "tollywood", "oscar", "grammy", "cannes film", "film festival",
    "box-office collection", "opening weekend",
)
_WEATHER = (
    "water level", "rainfall", "heavy rain", "monsoon", "heatwave", "heat wave",
    "cold wave", "flood alert", "flood warning", "cyclone", "low pressure", "depression over",
    "met office", "weather forecast", "waterlogging", "landslide warning",
)

# Country / place words that mark a story as foreign (own words are filtered out
# per edition before this is used).
_FOREIGN = (
    "bangladesh", "india", "pakistan", "nepal", "sri lanka", "myanmar", "china", "russia",
    "ukraine", "gaza", "israel", "palestin", "iran", "iraq", "afghanistan", "syria",
    "lebanon", "yemen", "turkey", "cyprus", "greece", "france", "germany", "italy",
    "spain", "portugal", "brazil", "argentina", "mexico", "canada", "australia", "japan",
    "china", "korea", "north korea", "vietnam", "thailand", "cambodia", "indonesia",
    "malaysia", "singapore", "nigeria", "kenya", "ethiopia", "sudan", "somalia",
    "south africa", "egypt", "morocco", "saudi", "uae", "dubai", "qatar", "kuwait",
    "ghana", "uganda", "zimbabwe", "jamaica", "new zealand", "tanzania", "zambia",
    "venezuela", "colombia", "peru", "chile", "poland", "sweden", "norway", "finland",
    "netherlands", "belgium", "switzerland", "united states", "washington", "moscow",
    "beijing", "tokyo", "seoul", "london", "paris", "berlin", "rome", "kyiv",
)


@lru_cache
def _category_matrix() -> np.ndarray:
    return embed_texts(list(_PROMPTS.values()))


def _unit_vec(headline: str, lead: str, embedding: list[float] | None) -> np.ndarray:
    if embedding is not None:
        vec = np.asarray(embedding, dtype=np.float32)
        n = float(np.linalg.norm(vec))
        return vec / n if n else vec
    text = f"{headline}. {lead[:240]}" if lead else headline
    return embed_texts([text])[0]


def _demote(cats: list[str], to: str, blocked: tuple[str, ...]) -> list[str]:
    """Replace a wrong primary with `to`, keeping a still-plausible secondary."""
    return [to, *[c for c in cats if c not in (to, *blocked)][:1]]


def categorize(
    headline: str,
    lead: str = "",
    country: str = "",
    embedding: list[float] | None = None,
) -> list[str]:
    haystack = f" {headline} {lead} ".lower()

    for cat, keywords in _OVERRIDES.items():
        if any(kw in haystack for kw in keywords):
            return [cat]

    scores = _category_matrix() @ _unit_vec(headline, lead, embedding)
    order = [int(i) for i in np.argsort(scores)[::-1]]
    ranked = [_KEYS[i] for i in order]
    top = float(scores[order[0]])

    cats = [ranked[0]]
    if float(scores[order[1]]) >= max(top * _SECONDARY_REL, _SECONDARY_MIN):
        cats.append(ranked[1])

    # "international" is a modifier, not a topic. Only keep / add it for a real
    # foreign angle; a purely domestic story gets its actual topic instead.
    own = _OWN.get(country, ())
    at_home = any(w in haystack for w in own)
    abroad = any(w in haystack for w in _FOREIGN if w not in own)

    if "international" in cats and not abroad:
        cats = [c for c in cats if c != "international"]
        for c in ranked:
            if c != "international" and c not in cats:
                cats.append(c)
                break
    elif cats[0] == "international" and at_home:
        # A story clearly about the home country is never *primarily* international,
        # even if it also touches a foreign player (e.g. "Japan boosts defence amid
        # China tension"). Demote it to a modifier behind the real topic.
        topic = next((c for c in ranked if c != "international"), "general")
        cats = [topic, "international"]
    elif "international" not in cats and abroad and not at_home:
        strong = any(w in haystack for w in _CONFLICT) or float(scores[_INTL]) >= _SECONDARY_MIN
        if strong:
            cats = [*cats, "international"][:2] if len(cats) < 2 else [cats[0], "international"]

    # Post-fixes for known embedding blind spots — run after the intl step so a
    # promoted primary is checked too.
    crime = any(w in haystack for w in _CRIME)
    violent = crime and any(
        w in haystack for w in (" dies", " died", "killed", "murder", "beaten", "stabbed",
                                "shot", "raped", "body found", "found dead")
    )
    if crime and cats[0] not in ("general", "international") and (
        cats[0] != "politics" or violent
    ):
        cats = _demote(cats, "general", ("technology", "politics"))
    if (
        cats[0] == "sports"
        and any(w in haystack for w in _AWARD)
        and not any(w in haystack for w in _SPORTS_CTX)
    ):
        cats = _demote(cats, "general", ("sports",))

    # Unambiguous topical signals the embedding missed (football transfers read
    # as "business", sports politics as "politics", box-office as "business").
    if cats[0] not in ("sports", "general") and any(w in haystack for w in _SPORT_STRONG):
        cats = _demote(cats, "sports", ())
    elif cats[0] not in ("entertainment", "general") and any(w in haystack for w in _ENT_STRONG):
        cats = _demote(cats, "entertainment", ())
    elif cats[0] not in ("general", "international") and any(w in haystack for w in _WEATHER):
        cats = _demote(cats, "general", ())

    out: list[str] = []
    for c in cats:
        if c and c not in out:
            out.append(c)
    return out[:2] or ["general"]
