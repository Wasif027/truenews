# TrueNews API. Portable across Render / Fly / Koyeb / Railway — they all run a
# Dockerfile. The GitHub Actions ingest cron installs the same package separately
# and doesn't use this image.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/tmp/hf

WORKDIR /app

# pyproject declares `packages = ["app"]`, so the source has to be present before
# `pip install .` can build it — copy both, then install.
COPY pyproject.toml ./
COPY app ./app
RUN pip install --no-cache-dir .

# The API itself never runs the embedding model (that's the GitHub Actions cron),
# but pre-fetch it so an image reused for a local ingest isn't slow on first use.
RUN python -c "from app.services.embeddings import embed_texts; embed_texts(['warm up'])"

# Hosts inject $PORT. Default 8000 for local `docker run`.
ENV PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
