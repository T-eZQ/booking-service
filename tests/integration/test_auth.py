import pytest
from httpx import AsyncClient


async def test_register_creates_employee_by_default(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "pass1234",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "alice"
    assert data["role"] == "employee"
    assert "hashed_password" not in data


async def test_register_duplicate_username_returns_409(client: AsyncClient):
    payload = {"username": "bob", "email": "bob@example.com", "password": "pass1234"}
    await client.post("/api/v1/auth/register", json=payload)
    resp = await client.post(
        "/api/v1/auth/register",
        json={**payload, "email": "bob2@example.com"},
    )
    assert resp.status_code == 409


async def test_register_duplicate_email_returns_409(client: AsyncClient):
    payload = {"username": "charlie", "email": "charlie@example.com", "password": "pass1234"}
    await client.post("/api/v1/auth/register", json=payload)
    resp = await client.post(
        "/api/v1/auth/register",
        json={**payload, "username": "charlie2"},
    )
    assert resp.status_code == 409


async def test_login_returns_token(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={"username": "dave", "email": "dave@example.com", "password": "mypassword"},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "dave", "password": "mypassword"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


async def test_login_wrong_password_returns_401(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={"username": "eve", "email": "eve@example.com", "password": "correct"},
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "eve", "password": "wrong"},
    )
    assert resp.status_code == 401


async def test_login_unknown_user_returns_401(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "nobody", "password": "whatever"},
    )
    assert resp.status_code == 401


async def test_get_me_returns_current_user(client: AsyncClient, employee_headers: dict):
    resp = await client.get("/api/v1/auth/me", headers=employee_headers)
    assert resp.status_code == 200
    assert resp.json()["username"] == "testemployee"


async def test_protected_endpoint_without_token_returns_403(client: AsyncClient):
    resp = await client.get("/api/v1/rooms")
    assert resp.status_code == 403
