from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.models  # noqa: F401 — registers all ORM models with metadata
from app.api.v1.router import router
from app.config import settings
from app.database import Base, async_session_factory, engine


async def _seed_initial_data() -> None:
    from app.core.security import hash_password
    from app.models.room import Room, TimeSlot
    from app.models.user import User, UserRole
    from app.repositories.room import RoomRepository
    from app.repositories.user import UserRepository

    async with async_session_factory() as session:
        async with session.begin():
            user_repo = UserRepository(session)

            if not await user_repo.get_by_username("admin"):
                session.add(
                    User(
                        username="admin",
                        email="admin@coworking.local",
                        hashed_password=hash_password("admin123"),
                        role=UserRole.ADMIN,
                    )
                )

            if not await user_repo.get_by_username("employee"):
                session.add(
                    User(
                        username="employee",
                        email="employee@coworking.local",
                        hashed_password=hash_password("employee123"),
                        role=UserRole.EMPLOYEE,
                    )
                )

            room_repo = RoomRepository(session)
            if not await room_repo.get_by_name("Переговорная Альфа"):
                room = Room(
                    name="Переговорная Альфа",
                    description="Просторная переговорная с проектором и маркерной доской",
                    capacity=10,
                )
                session.add(room)
                await session.flush()
                for start, end in [
                    ("09:00", "11:00"),
                    ("11:00", "13:00"),
                    ("13:00", "15:00"),
                    ("15:00", "17:00"),
                    ("17:00", "19:00"),
                ]:
                    session.add(TimeSlot(room_id=room.id, start_time=start, end_time=end))

            if not await room_repo.get_by_name("Переговорная Бета"):
                room = Room(
                    name="Переговорная Бета",
                    description="Камерная комната для переговоров 1:1 и небольших команд",
                    capacity=4,
                )
                session.add(room)
                await session.flush()
                for start, end in [
                    ("10:00", "12:00"),
                    ("12:00", "14:00"),
                    ("14:00", "16:00"),
                    ("16:00", "18:00"),
                ]:
                    session.add(TimeSlot(room_id=room.id, start_time=start, end_time=end))


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await _seed_initial_data()
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description=(
        "REST API for booking meeting rooms in a coworking space. "
        "Supports JWT authentication, role-based access (employee / admin), "
        "room and slot management, availability queries, and booking lifecycle."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
