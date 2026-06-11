import time

import pytest

from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hash_and_verify():
    password = "supersecret"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed)


def test_wrong_password_fails_verification():
    hashed = hash_password("correct")
    assert not verify_password("wrong", hashed)


def test_same_password_produces_different_hashes():
    p = "mypassword"
    assert hash_password(p) != hash_password(p)


def test_token_encode_and_decode():
    subject = "user-uuid-1234"
    token = create_access_token(subject)
    decoded = decode_access_token(token)
    assert decoded == subject


def test_invalid_token_returns_none():
    assert decode_access_token("not.a.valid.token") is None


def test_tampered_token_returns_none():
    token = create_access_token("some-user-id")
    parts = token.split(".")
    tampered = parts[0] + "." + parts[1] + ".invalidsignature"
    assert decode_access_token(tampered) is None
