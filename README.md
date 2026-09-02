# TrueNews

A web app that shows how a country's English-language press covers the same
stories. It aggregates news via RSS, groups articles about the same event into
one "story", and for each story shows a machine summary, a per-outlet breakdown
of how the coverage differs (framing, figures, what each outlet emphasised or
left out — written from the full article text, which is used and then discarded),
every outlet's own headline in order of publication, a coverage/blindspot
indicator, and links out to every original article.

**Countries:** 22 — Bangladesh, India, Pakistan, Nigeria, Philippines, UK, USA,
Australia, Ireland, Singapore, Malaysia, Canada, New Zealand, South Africa, Kenya,
Ghana, Uganda, Zimbabwe, Japan, Sri Lanka, Nepal, Jamaica (~130 outlets),
switchable in the header. Each is a config entry in
`backend/app/ingest/sources.py` plus its code in the `COUNTRIES` env var. The bar
for adding a country is at least three outlets with a working, current
English-language RSS feed.

See [SPEC.md](SPEC.md) for the full v1 scope and the reasoning behind it.

## Stack

| Layer | Choice |
|---|---|
| Ingestion | Python, hourly via GitHub Actions (`.github/workflows/ingest.yml`) |
| Embeddings / clustering | `fastembed` (BAAI/bge-small-en-v1.5, ONNX) + cosine-threshold connected components |
| Categorisation | zero-shot over the same embeddings; up to two categories per story |
| Summary + coverage comparison | up to 3 OpenAI-compatible LLM providers (`LLM_1_*`..`LLM_3_*`), tried in order and rolled over on any rate limit — chains free tiers (Gemini → Groq) so a busy day never drops the feature. Offline heuristic fallback with no key. |
| Loaded-language | transparent lexicon scorer (swappable for a BABE classifier) |
| Store | Postgres + pgvector |
| API | FastAPI |
| Frontend | Next.js (App Router) + Tailwind |

## Run it locally

Needs Python 3.11+, Node 20+, and any Postgres with the `vector` extension
(a free Neon database is easiest: put its URL in `backend/.env` as
`DATABASE_URL=postgresql+psycopg://...`).

### Everyday: one command

After the one-time setup below, start the API and the web app together from the
repo root:

```bash
npm run dev          # API on :8000, web on :3000, one terminal, Ctrl+C stops both
```

```bash
npm run ingest       # refresh the news now (fetch -> cluster -> summarise)
```

Set `INGEST_INTERVAL_MIN` in `backend/.env` to a positive number (e.g. `20`) and
the API re-ingests on that interval on its own, so new stories and the
"new stories" pill appear while you watch. The deployed version keeps this at `0`
and relies on the GitHub Actions cron (`.github/workflows/ingest.yml`, hourly) so
ingestion doesn't run twice against the same database.

Close any old `uvicorn` / `next dev` windows first so nothing double-binds a port.
(`npm run dev:api` / `npm run dev:web` run just one side.)

> The root scripts call the venv Python at `backend\.venv\Scripts\python` (Windows).
> On macOS / Linux change `dev:api` and `ingest` in the root `package.json` to
> `backend/.venv/bin/python`.

### One-time setup

### 1. Backend

macOS / Linux:

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install ".[dev]"
cp .env.example .env
docker compose up -d           # Postgres with pgvector on :5432
python -m app.cli verify-feeds # check the RSS URLs respond
python -m app.cli ingest       # fetch -> embed -> cluster -> summarise
uvicorn app.main:app --reload  # API on http://localhost:8000  (docs at /docs)
```

Windows (PowerShell) — run the lines one at a time, `&&` is not valid in PS 5.1:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1     # if blocked: Set-ExecutionPolicy -Scope Process -Bypass -Force
pip install ".[dev]"
Copy-Item .env.example .env
docker compose up -d
python -m app.cli verify-feeds
python -m app.cli ingest
uvicorn app.main:app --reload
```

Set at least one LLM slot in `.env` for real summaries — `LLM_1_KEY` / `LLM_1_BASE`
/ `LLM_1_MODEL` (a free Gemini or Groq key works). Leave them blank to use the
offline extractive fallback.

### 2. Frontend + root

```bash
cd frontend && npm install && cp .env.example .env.local   # PowerShell: Copy-Item .env.example .env.local
cd .. && npm install                                        # installs `concurrently` for `npm run dev`
```

Now use `npm run dev` from the repo root (see "Everyday" above).

### 3. Tests

```bash
cd backend
pytest -q
ruff check .
```

## Deploy (free tiers)

| Piece | Host | Notes |
|---|---|---|
| Database | Neon (has pgvector) | **pin compute to 0.25 CU** (set min = max, no autoscale) so 24/7 wake-time stays under the 191.9 compute-hours/month allowance; `DATABASE_URL` goes in the GitHub secret and the API host env |
| API | Render / Fly / Koyeb | builds from `backend/Dockerfile`; it runs `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Set `INGEST_INTERVAL_MIN=0`, a real `SECRET_KEY`, `COOKIE_SECURE=true`, `FRONTEND_ORIGIN` = the Vercel URL |
| Frontend | Vercel | root directory `frontend`; set `NEXT_PUBLIC_API_URL` to the API URL and `NEXT_PUBLIC_SITE_URL` to the Vercel URL |
| Ingestion | GitHub Actions cron (`ingest.yml`, hourly) | **public repo required**; add `DATABASE_URL`, `LLM_1_KEY`, `LLM_2_KEY` as repo secrets |

The API image pre-fetches the embedding model at build time, so the first request
is fast. Kick off the first ingest from the repo's Actions tab ("Run workflow" →
`ingest`); the full per-outlet comparisons fill in over the next few cron runs.

## `npm run` shortcuts

`dev`, `ingest`, `reset`, `recategorize` (re-run the category rules + clear
summaries after editing them), `verify-feeds`.

## Status vs SPEC

Done: 22-country ingestion + switcher, embedding clustering with near-duplicate
(wire-copy / syndication) collapsing, two-category zero-shot categorisation, LLM
summary + full per-outlet coverage comparison (offline fallback), multi-select
category filter with counts that track the single-source toggle, search,
hot/recent sort, single-source handling, read-at-source, time-ordered headline
comparison, coverage/blindspot, loaded-language flags, dark/light, status page,
infinite scroll, "new stories" pill, rolling data prune (keeps saved/liked
stories), username/password auth (bcrypt + JWT in an httpOnly cookie), per-user
like / save / 20-item history, API docs, CI.

Not yet: developing-story timeline UI, and the v2 outlet-analytics dashboard.
