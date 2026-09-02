"""Full auth + like/save/history flow against a real database.

Skipped unless RUN_DB_TESTS=1 (CI sets it, with a Postgres service). Locally it
would write test rows to whatever DATABASE_URL points at, so it stays off.
"""

import os
import uuid
from datetime import UTC

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_DB_TESTS") != "1", reason="set RUN_DB_TESTS=1 to run"
)


@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from sqlalchemy import text

    from app.db import engine, init_db
    from app.main import app

    init_db()
    yield TestClient(app)

    with engine.begin() as c:
        c.execute(text("delete from \"like\" where user_id in (select id from app_user where username like 'qa\\_%')"))
        c.execute(text("delete from save where user_id in (select id from app_user where username like 'qa\\_%')"))
        c.execute(text("delete from visit where user_id in (select id from app_user where username like 'qa\\_%')"))
        c.execute(text("delete from app_user where username like 'qa\\_%'"))
        c.execute(text("delete from cluster where canonical_title like 'auth-test story %'"))


def _seed_story():
    """Insert one cluster directly so the flow has something to act on."""
    from datetime import datetime

    from sqlalchemy import text

    from app.db import engine

    with engine.begin() as c:
        c.execute(
            text(
                "insert into cluster (country, canonical_title, category, created_at, "
                "updated_at, outlet_count, article_count, hotness) values "
                "('bd', :t, 'general', :n, :n, 1, 1, 1.0)"
            ),
            {"t": f"auth-test story {uuid.uuid4()}", "n": datetime.now(UTC)},
        )
        return c.execute(text("select max(id) from cluster")).scalar()


def test_full_flow(client):
    name = f"qa_{uuid.uuid4().hex[:10]}"
    assert client.post("/api/auth/signup", json={"username": name, "password": "hunter2xx"}).status_code == 200
    assert client.get("/api/auth/me").json()["username"] == name

    sid = _seed_story()
    assert client.put(f"/api/stories/{sid}/like").status_code == 200
    assert client.post(f"/api/stories/{sid}/visit").status_code == 200

    assert client.get(f"/api/stories/{sid}/me").json() == {"liked": True, "saved": False}
    assert [s["id"] for s in client.get("/api/me/likes").json()] == [sid]
    assert sid in [s["id"] for s in client.get("/api/me/history").json()]

    client.put(f"/api/stories/{sid}/like?on=false")
    assert client.get("/api/me/likes").json() == []
    assert client.get(f"/api/stories/{sid}/me").json()["liked"] is False


def test_auth_guards(client):
    # A fresh TestClient with no auth cookie set.
    assert client.get("/api/auth/me").status_code == 401
    assert client.put("/api/stories/1/like").status_code == 401
    assert client.post("/api/auth/login", json={"username": "nope", "password": "nope"}).status_code == 401
