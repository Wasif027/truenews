from app.security import _user_id_from_token, hash_password, make_token, verify_password


def test_password_hash_roundtrip():
    h = hash_password("correct horse battery")
    assert h != "correct horse battery"
    assert verify_password("correct horse battery", h)
    assert not verify_password("wrong", h)


def test_token_roundtrip():
    token = make_token(42)
    assert _user_id_from_token(token) == 42


def test_bad_token_returns_none():
    assert _user_id_from_token("not-a-jwt") is None
    assert _user_id_from_token("") is None
