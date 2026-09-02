"""Real-embedding clustering check. Skipped by default (downloads a model);
run with RUN_EMBED_TESTS=1 or in CI where fastembed is installed."""

import os

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_EMBED_TESTS") != "1", reason="set RUN_EMBED_TESTS=1 to run"
)


def test_same_story_clusters_and_unrelated_does_not():
    from app.services.clustering import cluster_by_similarity
    from app.services.embeddings import embed_texts

    headlines = [
        "Govt to relocate Karwan Bazar kitchen market",           # 0 \
        "PM instructs Karwan Bazar kitchen market relocation",     # 1  } same story
        "PM asks for shifting Karwan Bazar kitchen market",        # 2 /
        "Messi's four-goal masterclass helps Miami snap streak",   # 3  unrelated
        "Dengue cases rise sharply in Chittagong",                 # 4  unrelated
    ]
    emb = embed_texts(headlines)
    groups = cluster_by_similarity(list(range(len(headlines))), emb, threshold=0.80)
    by_member = {i: sorted(g) for g in groups for i in g}

    assert by_member[0] == [0, 1, 2]
    assert by_member[3] == [3]
    assert by_member[4] == [4]
