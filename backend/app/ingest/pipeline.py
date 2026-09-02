from __future__ import annotations

import logging
import math
import re
from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta

import numpy as np
from sqlalchemy import text, update
from sqlmodel import Session, select

from app.config import get_settings
from app.db import engine, init_db
from app.ingest.rss import fetch_feed
from app.ingest.sources import sources_for
from app.models import Article, Cluster, FlaggedSentence, Outlet, utcnow
from app.services import extract
from app.services.categorize import categorize
from app.services.clustering import cluster_by_similarity, medoid_index
from app.services.embeddings import embed_texts
from app.services.loaded_language import flag_text
from app.services.summarize import SourceItem, summarise

log = logging.getLogger("truenews.pipeline")


def _sync_outlets(session: Session, country: str) -> dict[str, Outlet]:
    existing = {o.slug: o for o in session.exec(select(Outlet).where(Outlet.country == country))}
    for cfg in sources_for(country):
        o = existing.get(cfg.slug)
        if o is None:
            o = Outlet(country=country, slug=cfg.slug, name=cfg.name,
                       homepage=cfg.homepage, rss_url=cfg.feeds[0])
            session.add(o)
        else:
            o.name, o.homepage, o.rss_url = cfg.name, cfg.homepage, cfg.feeds[0]
        existing[cfg.slug] = o
    session.commit()  # session has expire_on_commit=False, so .id stays loaded
    return existing


def _ingest_articles(session: Session, country: str, outlets: dict[str, Outlet]) -> list[Article]:
    # Global, not per-country: `article.url` is unique across the whole table, and
    # some outlets syndicate (e.g. Guardian UK / Guardian AU run the same piece).
    known_urls = set(session.exec(select(Article.url)).all())
    new: list[Article] = []
    for cfg in sources_for(country):
        outlet = outlets[cfg.slug]
        for raw in fetch_feed(cfg):
            if raw.url in known_urls:
                continue
            known_urls.add(raw.url)
            session.add(
                art := Article(
                    outlet_id=outlet.id,
                    country=country,
                    url=raw.url,
                    headline=raw.headline,
                    byline=raw.byline,
                    lead_text=raw.lead_text,
                    category=raw.category,
                    published_at=raw.published_at,
                )
            )
            new.append(art)
    session.commit()
    log.info("ingested %d new articles", len(new))
    return new


def _cat_text(a: Article) -> str:
    return f"{a.headline}. {(a.lead_text or '')[:240]}"


def _cluster_cats(arts: list[Article]) -> tuple[str, str | None]:
    """A cluster's category from its articles: primaries weighted 2, secondaries 1.
    A secondary is kept only if it has real support across the coverage."""
    tally: Counter[str] = Counter()
    for a in arts:
        tally[a.category] += 2
        if a.category_secondary:
            tally[a.category_secondary] += 1
    ranked = tally.most_common()
    primary = ranked[0][0]
    for cat, weight in ranked[1:]:
        if weight >= max(2, len(arts) * 0.5):
            return primary, cat
    return primary, None


def _embed_new(session: Session, articles: list[Article]) -> None:
    if not articles:
        return
    # Clustering embedding: headline only. Including the lead collapsed similarities
    # (truncated / missing leads across outlets pulled everything together).
    vecs = embed_texts([a.headline for a in articles])
    # Categorisation embedding: headline + lead. Headlines alone are too short for
    # the tiny model to separate topics reliably.
    cat_vecs = embed_texts([_cat_text(a) for a in articles])
    for art, vec, cvec in zip(articles, vecs, cat_vecs, strict=True):
        art.embedding = vec.tolist()
        cats = categorize(art.headline, art.lead_text or "", art.country, cvec.tolist())
        art.category = cats[0]
        art.category_secondary = cats[1] if len(cats) > 1 else None
    session.commit()


def _hotness(outlet_count: int, article_count: int, newest: datetime) -> float:
    hours = max(0.0, (datetime.now(UTC) - newest).total_seconds() / 3600)
    recency = math.exp(-hours / 24.0)
    return round((outlet_count + math.log1p(article_count)) * recency, 4)


_NORM_RE = re.compile(r"[^a-z0-9]+")


def _norm_headline(text: str) -> str:
    return _NORM_RE.sub("", (text or "").lower())


def _effective_outlets(rows: list[tuple[int, str]]) -> int:
    """How many *independent* newsrooms covered a story, given (outlet_id,
    headline) pairs for its articles. Wire copy and publisher-group syndication
    (e.g. the same national piece under two mastheads) share a headline, so they
    collapse to one; an outlet running several distinct angles still counts once.
    = min(distinct normalised headlines, distinct outlets)."""
    if not rows:
        return 0
    heads = {_norm_headline(h) for _, h in rows if h and h.strip()}
    outlets = {oid for oid, _ in rows}
    # An article with an empty headline still contributes its outlet.
    n_heads = len(heads) or len(outlets)
    return min(n_heads, len(outlets))


def _recompute_counts(session: Session, country: str) -> None:
    """Make every cluster's counts match actual article membership. Clears the
    counts of clusters that lost all their articles to a merge, so they drop out
    of the feed (which filters on article_count > 0). `outlet_count` is the
    *independent-newsroom* count (see `_effective_outlets`), not raw distinct
    outlet ids, so syndicated copy doesn't inflate a story to "multi-source"."""
    members: dict[int, list[tuple[int, str]]] = defaultdict(list)
    for cid, oid, headline in session.execute(
        select(Article.cluster_id, Article.outlet_id, Article.headline).where(
            Article.country == country, Article.cluster_id.is_not(None)
        )
    ).all():
        members[cid].append((oid, headline))

    for cluster in session.exec(select(Cluster).where(Cluster.country == country)).all():
        rows = members.get(cluster.id, [])
        cluster.article_count = len(rows)
        cluster.outlet_count = _effective_outlets(rows)
    session.commit()


def _recluster(session: Session, country: str) -> list[Cluster]:
    s = get_settings()
    cutoff = utcnow() - timedelta(hours=s.cluster_window_hours)
    rows = session.exec(
        select(Article).where(
            Article.country == country,
            Article.published_at >= cutoff,
            Article.embedding.is_not(None),  # type: ignore[union-attr]
        )
    ).all()
    if not rows:
        return []

    by_id = {a.id: a for a in rows}
    ids = [a.id for a in rows]
    emb = np.array([a.embedding for a in rows], dtype=np.float32)
    groups = cluster_by_similarity(ids, emb, s.cluster_sim_threshold)

    # 1. decide: reuse an existing cluster, or mint a new one
    plans: list[list] = []  # [articles, cluster_or_None]
    for group in groups:
        arts = [by_id[i] for i in group]
        existing_ids = [a.cluster_id for a in arts if a.cluster_id is not None]
        cluster: Cluster | None = None
        if existing_ids:
            dominant, dom_count = Counter(existing_ids).most_common(1)[0]
            cand = session.get(Cluster, dominant)
            # Reuse only if this group is a real chunk of that cluster, not a
            # fragment split off an over-merged blob by a stricter threshold.
            if cand and dom_count >= 0.5 * max(cand.article_count, 1):
                cluster = cand
        plans.append([arts, cluster])

    # 2. bulk-create the new clusters in one round trip
    to_create = [p for p in plans if p[1] is None]
    created = [Cluster(country=country, canonical_title=p[0][0].headline) for p in to_create]
    session.add_all(created)
    session.flush()
    for plan, cluster in zip(to_create, created, strict=True):
        plan[1] = cluster

    # 3. fill in cluster fields and article membership
    touched: list[Cluster] = []
    for arts, cluster in plans:
        g_emb = np.array([a.embedding for a in arts], dtype=np.float32)
        central = arts[medoid_index(g_emb)]
        earliest = min(arts, key=lambda a: a.published_at)
        newest = max(a.published_at for a in arts)
        for a in arts:
            a.cluster_id = cluster.id
        cluster.canonical_title = central.headline
        cluster.category, cluster.category_secondary = _cluster_cats(arts)
        cluster.first_article_id = earliest.id
        cluster.hotness = _hotness(
            _effective_outlets([(a.outlet_id, a.headline) for a in arts]), len(arts), newest
        )
        # "Updated" = the most recent time an outlet published on this story, not
        # the time this job ran — otherwise every story reads as "just now" after
        # each ingest. Clamp to now so a feed with a bad future date can't pin a
        # story to the top forever.
        cluster.updated_at = min(newest, utcnow())
        touched.append(cluster)

    session.commit()
    _recompute_counts(session, country)
    log.info("reclustered window: %d stories touched", len(touched))
    return touched


def _summarise_clusters(session: Session, clusters: list[Cluster]) -> None:
    budget = get_settings().summary_budget_per_run
    ranked = sorted(clusters, key=lambda c: c.hotness, reverse=True)
    if not ranked:
        return

    names = {o.id: o.name for o in session.exec(select(Outlet))}
    arts_by_cluster: dict[int, list[Article]] = defaultdict(list)
    for a in session.exec(
        select(Article).where(Article.cluster_id.in_([c.id for c in ranked]))  # type: ignore[union-attr]
    ):
        arts_by_cluster[a.cluster_id].append(a)

    def _pick_per_outlet(arts: list[Article]) -> list[Article]:
        chosen: dict[int, Article] = {}
        for a in arts:
            cur = chosen.get(a.outlet_id)
            if cur is None or len(a.lead_text) > len(cur.lead_text):
                chosen[a.outlet_id] = a
        return list(chosen.values())

    def _needs_summary(c: Cluster) -> bool:
        arts = arts_by_cluster.get(c.id, [])
        if not arts:
            return False
        sig = ",".join(map(str, sorted({a.outlet_id for a in arts})))
        return not (c.summary and c.summarised_outlet_ids == sig)

    todo = [c for c in ranked if _needs_summary(c)]
    have_key = bool(get_settings().llm_providers)
    # The hottest `budget` get the model (full comparison, from the article
    # bodies); everything else in the window still gets the offline summary +
    # one-line comparison so no story is left blank.
    llm_ids = {c.id for c in todo[:budget]} if have_key else set()

    if llm_ids:
        need = [
            a.url
            for c in todo
            if c.id in llm_ids
            for a in _pick_per_outlet(arts_by_cluster.get(c.id, []))
        ]
        session.commit()  # don't hold a transaction open across the fetch batch
        extract.prefetch(need)

    done = 0
    for cluster in todo:
        arts = arts_by_cluster[cluster.id]
        signature = ",".join(map(str, sorted({a.outlet_id for a in arts})))
        use_llm = cluster.id in llm_ids

        picked = _pick_per_outlet(arts)
        if use_llm and len(picked) > 5:
            # Cap the LLM input: 5 outlets is plenty, free-tier tokens are the
            # bottleneck. Keep the ones that ran it first.
            picked = sorted(picked, key=lambda a: a.published_at)[:5]
        items = [
            SourceItem(
                outlet=names.get(a.outlet_id, "Unknown"),
                headline=a.headline,
                lead=a.lead_text,
                # ~900 chars ≈ the first few paragraphs — enough to see framing.
                body=extract.article_text(a.url)[:900] if use_llm else "",
            )
            for a in picked
        ]
        result = summarise(items, use_llm=use_llm)
        cluster.summary = result.summary
        cluster.coverage_diff = result.coverage_diff if len(items) > 1 else None
        cluster.coverage_detail = result.coverage_detail if len(items) > 1 else None
        # The model reads the whole article, so its category call beats the
        # ingest-time embedding guess — trust it for the stories it summarises.
        if result.categories:
            cluster.category = result.categories[0]
            cluster.category_secondary = (
                result.categories[1] if len(result.categories) > 1 else None
            )
        # Mark done. A story we meant to run through the model but couldn't
        # (rate-limited -> offline) gets a "~" marker so a later run retries it
        # for the full comparison instead of skipping it forever.
        soft = use_llm and result.via != "llm"
        cluster.summarised_outlet_ids = f"{signature}~" if soft else signature
        done += 1
        # Commit as we go: a long LLM batch would otherwise hold one transaction
        # open for minutes (Neon drops idle-in-transaction connections), and a
        # mid-batch failure would lose everything.
        if done % 20 == 0:
            session.commit()
    session.commit()
    log.info("summarised %d stories (%d via model)", done, len(llm_ids))


def _flag_new(session: Session, articles: list[Article]) -> None:
    for art in articles:
        for flag in flag_text(art.lead_text):
            session.add(FlaggedSentence(article_id=art.id, text=flag.text, score=flag.score))
    session.commit()


def _prune_old(session: Session, country: str) -> None:
    """Drop articles we fetched more than (window + 4 days) ago, and any cluster
    left empty — the feed only looks at the last ~4 days anyway. Clusters a user
    has saved or liked are kept indefinitely so their Saved tab keeps working."""
    cutoff = utcnow() - timedelta(hours=get_settings().cluster_window_hours + 96)
    # article ids that are old AND whose cluster nobody has kept
    old_articles = (
        "select a.id from article a where a.country = :c and a.fetched_at < :cut "
        "and (a.cluster_id is null or a.cluster_id not in ("
        "  select cluster_id from \"like\" union select cluster_id from save))"
    )
    p = {"c": country, "cut": cutoff}
    session.execute(
        text(f"delete from flagged_sentence where article_id in ({old_articles})"), p
    )
    removed = session.execute(
        text(f"delete from article where id in ({old_articles})"), p
    ).rowcount
    session.commit()
    _recompute_counts(session, country)
    dead = session.execute(
        text(
            "delete from cluster where country = :c and article_count = 0 "
            'and id not in (select cluster_id from "like" union select cluster_id from save)'
        ),
        {"c": country},
    ).rowcount
    session.commit()
    if removed or dead:
        log.info("pruned %d old articles, %d empty clusters", removed, dead)


def recategorize() -> dict:
    """Re-run category detection on every stored article, refresh each cluster's
    category, and clear cached summaries so they regenerate. Run once after
    changing the category rules or the summary prompt."""
    init_db()
    # Phase 1: read the rows, then close the connection. The embedding pass below
    # takes minutes and Neon kills a connection left idle-in-transaction.
    with Session(engine) as session:
        rows = session.execute(
            select(
                Article.id, Article.headline, Article.lead_text, Article.country,
                Article.cluster_id, Article.category, Article.category_secondary,
            )
        ).all()

    # Phase 2: pure compute, no DB connection held.
    decided: dict[int, tuple[str, str | None]] = {}
    moves: dict[tuple[str, str | None], list[int]] = defaultdict(list)
    for i in range(0, len(rows), 256):
        chunk = rows[i : i + 256]
        vecs = embed_texts([f"{h}. {(ld or '')[:240]}" for _, h, ld, *_ in chunk])
        for (aid, h, ld, country, _cid, old1, old2), v in zip(chunk, vecs, strict=True):
            cats = categorize(h, ld or "", country or "", v.tolist())
            new = (cats[0], cats[1] if len(cats) > 1 else None)
            decided[aid] = new
            if new != (old1, old2):
                moves[new].append(aid)

    members: dict[int, Counter[str]] = defaultdict(Counter)
    sizes: Counter[int] = Counter()
    for row in rows:
        cid = row[4]
        if cid is None:
            continue
        sizes[cid] += 1
        p, s = decided[row[0]]
        members[cid][p] += 2
        if s:
            members[cid][s] += 1

    # Phase 3: fresh connection, quick writes.
    with Session(engine, expire_on_commit=False) as session:
        for (p, s), ids in moves.items():
            for j in range(0, len(ids), 500):
                session.execute(
                    update(Article)
                    .where(Article.id.in_(ids[j : j + 500]))  # type: ignore[attr-defined]
                    .values(category=p, category_secondary=s)
                )
        session.commit()
        changed = sum(len(v) for v in moves.values())

        for cluster in session.exec(select(Cluster).where(Cluster.article_count > 0)).all():
            tally = members.get(cluster.id)
            if tally:
                ranked = tally.most_common()
                cluster.category = ranked[0][0]
                cluster.category_secondary = next(
                    (c for c, w in ranked[1:] if w >= max(2, sizes[cluster.id] * 0.5)), None
                )
            cluster.summary = None
            cluster.coverage_diff = None
            cluster.coverage_detail = None
            cluster.summarised_outlet_ids = None
        session.commit()

    log.info("recategorized: %d/%d articles changed category", changed, len(rows))
    return {"articles": len(rows), "changed": changed}


def run(country: str | None = None) -> dict:
    country = country or get_settings().default_country
    init_db()
    with Session(engine, expire_on_commit=False) as session:
        outlets = _sync_outlets(session, country)
        new_articles = _ingest_articles(session, country, outlets)
        _embed_new(session, new_articles)
        touched = _recluster(session, country)
        _summarise_clusters(session, touched)
        _flag_new(session, new_articles)
        _prune_old(session, country)
        return {
            "country": country,
            "new_articles": len(new_articles),
            "stories_touched": len(touched),
            "ran_at": utcnow().isoformat(),
        }


def run_all() -> list[dict]:
    """Ingest every configured country, one after another."""
    results = []
    for country in get_settings().country_list:
        try:
            results.append(run(country))
        except Exception:
            log.exception("ingest failed for %s", country)
            results.append({"country": country, "error": True})
    return results
