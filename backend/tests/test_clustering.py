import numpy as np

from app.services.clustering import cluster_by_similarity, medoid_index


def _norm(v):
    v = np.array(v, dtype=np.float32)
    return v / np.linalg.norm(v)


def test_groups_similar_and_splits_dissimilar():
    a1 = _norm([1.0, 0.0, 0.0])
    a2 = _norm([0.97, 0.05, 0.0])
    b1 = _norm([0.0, 1.0, 0.0])
    emb = np.array([a1, a2, b1])
    groups = cluster_by_similarity([10, 11, 12], emb, threshold=0.8)
    as_sets = sorted((sorted(g) for g in groups), key=len, reverse=True)
    assert [10, 11] in as_sets
    assert [12] in as_sets


def test_singletons_when_threshold_high():
    emb = np.array([_norm([1, 0, 0]), _norm([0.6, 0.8, 0]), _norm([0, 0, 1])])
    groups = cluster_by_similarity([1, 2, 3], emb, threshold=0.99)
    assert sorted(len(g) for g in groups) == [1, 1, 1]


def test_medoid_picks_central_row():
    emb = np.array([_norm([1, 0, 0]), _norm([0.9, 0.1, 0]), _norm([0.2, 0.98, 0])])
    assert medoid_index(emb) in (0, 1)
