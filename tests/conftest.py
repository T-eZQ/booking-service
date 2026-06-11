import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncSession:
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_engine) -> AsyncClient:
    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            async with session.begin():
                yield session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def employee_headers(client: AsyncClient) -> dict:
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "testemployee",
            "email": "testemployee@example.com",
            "password": "password123",
            "role": "employee",
        },
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "testemployee", "password": "password123"},
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest_asyncio.fixture
async def admin_headers(client: AsyncClient) -> dict:
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "testadmin",
            "email": "testadmin@example.com",
            "password": "password123",
            "role": "admin",
        },
    )
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "testadmin", "password": "password123"},
    )
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest_asyncio.fixture
async def sample_room(client: AsyncClient, admin_headers: dict) -> dict:
    resp = await client.post(
        "/api/v1/rooms",
        json={
            "name": "Test Room",
            "description": "A room for tests",
            "capacity": 6,
            "slots": [
                {"start_time": "09:00", "end_time": "11:00"},
                {"start_time": "13:00", "end_time": "15:00"},
            ],
        },
        headers=admin_headers,
    )
    return resp.json()
