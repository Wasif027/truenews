# TrueNews — v1 Spec

## What it is

A web app that shows how a country's English-language press covers the same
stories. It aggregates news, groups articles about the same event into one
"story", and for each story shows a summary, every outlet covering it, how the
coverage differs, and links out to every original article.

**Launch country:** Bangladesh (country is a config file — more countries are v2).
**Language:** English.
**Goal:** a live portfolio demo (GitHub repo + demo URL). Not a store launch, no
real-user target. Every feature must be explainable in a technical interview.

## What it does NOT do

- No comments / user-generated content
- No left/right political labels
- No claim about whether a story is *true* — only how it is *covered*
- No scraping of full article text — RSS metadata + short lead paragraph only

---

## v1 features (user-facing)

### Story feed
- Feed of today's stories. A "story" = a **cluster** of articles from different
  outlets about the same event.
- **"Top today"** view — stories ranked by number of outlets + pickup speed.
- **Browse by category** — politics, business, sports, domestic, international, …
  (from the RSS section; fallback zero-shot classifier).
- **Search** across story clusters (Postgres full-text).
- **Dark / light toggle** — defaults to system preference, remembered in
  `localStorage`.

### Per story
- **AI summary** (generated once, cached).
- **"How coverage differs"** — 1–2 sentences generated in the *same* LLM call as
  the summary, from each source's headline + first paragraph. Constrained to
  factual differences only: framing words, differing numbers, what one outlet
  includes that others omit.
- **Headline framing comparison** — every outlet's own headline stacked side by
  side.
- **Coverage indicator** — "6 of 10 tracked outlets reported this", plus which
  ones did not (blindspot signal).
- **"Who broke it"** badge — outlet with the earliest timestamp in the cluster.
- **Developing-story timeline** — the cluster's articles plotted over time; the
  cluster shows an "updated" flag when a new article joins.
- **Loaded-language highlighting** — charged / emotive sentences flagged
  (BABE-style model), with a rough neutral-vs-slanted read.

### Read at source
- **"Read at source"** → picker listing each outlet with its headline, byline,
  timestamp, (reading time / paywall flag if detectable). Opens the original in
  a new tab. Nothing scraped.

### Single-outlet stories
- Shown, framed neutrally: **"Reported by 1 of 10 tracked outlets · not yet
  corroborated"**.
- No "how coverage differs" block.
- Show the outlet's own lead paragraph + link instead of an AI summary (cheaper,
  zero hallucination risk, maximally copyright-safe).
- Ranked lower in "Top today".
- Filter toggle: **"Hide single-source stories"**.

### Account (minimal)
- Auth (email or OAuth).
- **Save** / **like** a story.
- **Share** — share link points to the *original* article, not the app.

### Country switcher
- Shows "Bangladesh" now. Built so adding a country = adding a config file
  (sources, RSS URLs, categories, government actors to track).

### Supporting pages
- **"How it works" / methodology page** — plain-English explanation of
  clustering, coverage-gap analysis, loaded-language detection. Doubles as the
  answer to "how does your bias detection work?"
- **Pipeline status page** — last ingestion run, articles ingested, clusters
  formed.
- **Auto-generated API docs** (free with FastAPI).

---

## Architecture

```
GitHub Actions (hourly cron)
  └─ ingestion script
       fetch RSS (~10 outlets)
       parse + dedupe articles
       embed headlines (all-MiniLM-L6-v2 / bge-small-en)
       cluster same-event articles (cosine sim + connected components / HDBSCAN)
       for each NEW cluster: summary + "how coverage differs" (one free LLM call)
       loaded-language pass on each article
       write to Postgres

API (FastAPI, Render/Railway free tier)
  └─ serves stories, clusters, categories, search from Postgres

Frontend (React / Next, Vercel)
  └─ reader UI
```

All free tiers. LLM cost near zero: summarize each cluster once, ever; cap at
~40 clusters/day.

### Free model / service choices
| Task | Choice |
|---|---|
| Embeddings / clustering | `all-MiniLM-L6-v2` or `bge-small-en` (local, CPU) |
| Summary + coverage-diff | Gemini Flash free tier, or Groq free tier (Llama) |
| Loaded-language detection | BABE-trained classifier (Hugging Face) |
| Category fallback | `facebook/bart-large-mnli` zero-shot |
| Journalist / date / source | straight from RSS metadata |

---

## Data model (sketch)

- **outlet** — id, name, homepage, rss_url, country
- **article** — id, outlet_id, url, headline, byline, published_at, lead_text,
  category, embedding, fetched_at
- **cluster** — id, country, canonical_title, category, created_at, updated_at,
  first_article_id, summary, coverage_diff, outlet_count
- **cluster_article** — cluster_id, article_id
- **flagged_sentence** — article_id, text, score
- **user** — id, email, …
- **saved** / **liked** — user_id, cluster_id, created_at

---

## Build phases

1. **Ingestion core** — RSS fetch + parse for ~10 BD outlets → Postgres. Cron via
   GitHub Actions.
2. **Clustering** — embeddings + same-event grouping. Tune threshold on real
   headlines. This is the hardest part; get it right.
3. **Summary + coverage-diff** — one cached LLM call per new cluster.
4. **API** — serve clusters, stories, categories, search.
5. **Frontend** — feed, story page, read-at-source picker, headline comparison,
   dark/light, search.
6. **Loaded-language pass** + methodology page.
7. **Auth + save/like/share.**
8. **Polish** — status page, API docs, tests, CI, deploy demo URL.

v2 candidates: outlet analytics dashboard, blindspot feed, entity-sentiment
over time, number/claim comparison, second country, daily digest.

---

## Implementation notes (from the build, 2026-08)

- **Usable BD English RSS is scarcer than expected.** Shipped with 5 outlets that
  have fresh, parseable feeds: The Daily Star (5 section feeds), Dhaka Tribune,
  The Business Standard (3 section feeds), Prothom Alo English, The Daily
  Observer. Excluded: bdnews24 / Daily Sun / Bangladesh Post (Cloudflare 403 to
  server requests), New Age (no feed), Financial Express (malformed XML). An
  outlet can carry several section feeds — the main feeds of Daily Star and TBS
  are stale, only the section feeds are live.
- **Clustering: embed the headline only, not headline + lead.** Including the
  lead collapsed all pairwise similarities (truncated/absent leads across outlets
  dragged everything together). Headline-only cosine on bge-small-en-v1.5 has a
  healthy spread (mean ~0.43, p99 ~0.63); the link threshold is **0.80**
  (`CLUSTER_SIM_THRESHOLD`), tuned against a live pull of ~230 articles.
- A future fallback for bot-blocked outlets: Google News per-site RSS
  (`news.google.com/rss/search?q=site:<domain>+when:1d`).
