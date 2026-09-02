from __future__ import annotations

import logging
import os
import tempfile
from functools import lru_cache
from pathlib import Path

import numpy as np

from app.config import get_settings

log = logging.getLogger("truenews.embeddings")

# Once the model is cached on disk, skip Hugging Face's network check on every
# load — it was adding minutes per ingestion run.
_cache = Path(tempfile.gettempdir()) / "fastembed_cache"
if _cache.exists() and any(_cache.glob("models--*/snapshots/*/*.onnx")):
    os.environ.setdefault("HF_HUB_OFFLINE", "1")


@lru_cache
def _model():
    # fastembed uses an ONNX runtime — no torch, small install, CI-friendly.
    from fastembed import TextEmbedding

    name = get_settings().embedding_model
    log.info("loading embedding model %s", name)
    return TextEmbedding(model_name=name)


def embed_texts(texts: list[str]) -> np.ndarray:
    """Return L2-normalised embeddings, shape (len(texts), dim)."""
    if not texts:
        return np.zeros((0, get_settings().embedding_dim), dtype=np.float32)
    vecs = np.array(list(_model().embed(texts)), dtype=np.float32)
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vecs / norms


def embed_one(text: str) -> list[float]:
    return embed_texts([text])[0].tolist()
