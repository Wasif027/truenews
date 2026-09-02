# TrueNews API. Portable across Render / Fly / Koyeb / Railway — they all run a
# Dockerfile. The GitHub Actions ingest cron installs the same package separately
# and doesn't use this image.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/tmp/hf

WORKDIR /app

# Install deps first so the layer caches when only app code changes.
COPY pyproject.toml ./
RUN pip install --no-cache-dir .

COPY app ./app

# The embedding model (~90 MB) downloads on first use; pre-fetch it into the
# image so the first request isn't slow.
RUN python -c "from app.services.embeddings import embed_texts; embed_texts(['warm up'])"

# Hosts inject $PORT. Default 8000 for local `docker run`.
ENV PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
