"""Same-event clustering.

Approach (deliberately simple and explainable — see /how-it-works):

1. Take every article inside a rolling time window.
2. Embed headline + lead, L2-normalise, so dot product == cosine similarity.
3. Link any two articles with similarity >= threshold.
4. Connected components of that graph = stories.

Trade-offs: single linkage can chain loosely related items when the threshold is
too low; too high and the same event from two outlets stays split. The threshold
is config (CLUSTER_SIM_THRESHOLD) and is the main thing to tune on real data.
"""

from __future__ import annotations

import numpy as np


class _UnionFind:
    def __init__(self, n: int) -> None:
        self.parent = list(range(n))

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra


def cluster_by_similarity(
    ids: list[int], embeddings: np.ndarray, threshold: float
) -> list[list[int]]:
    """Return a list of clusters, each a list of article ids. Order within a
    cluster follows the input order."""
    n = len(ids)
    if n == 0:
        return []
    if n == 1:
        return [[ids[0]]]

    sim = embeddings @ embeddings.T
    uf = _UnionFind(n)
    linked = np.argwhere(np.triu(sim >= threshold, k=1))
    for i, j in linked:
        uf.union(int(i), int(j))

    groups: dict[int, list[int]] = {}
    for idx, art_id in enumerate(ids):
        groups.setdefault(uf.find(idx), []).append(art_id)
    return list(groups.values())


def medoid_index(embeddings: np.ndarray) -> int:
    """Index of the most central row (highest mean similarity to the rest)."""
    if len(embeddings) == 1:
        return 0
    sim = embeddings @ embeddings.T
    np.fill_diagonal(sim, 0.0)
    return int(sim.mean(axis=1).argmax())
