from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.room import Room, TimeSlot


class RoomRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_all(self) -> list[Room]:
        result = await self.session.execute(
            select(Room).options(selectinload(Room.slots)).order_by(Room.name)
        )
        return list(result.scalars().all())

    async def get_by_id(self, room_id: UUID) -> Room | None:
        result = await self.session.execute(
            select(Room).options(selectinload(Room.slots)).where(Room.id == room_id)
        )
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Room | None:
        result = await self.session.execute(select(Room).where(Room.name == name))
        return result.scalar_one_or_none()

    async def create(self, room: Room) -> Room:
        self.session.add(room)
        await self.session.flush()
        await self.session.refresh(room)
        return room

    async def update(self, room: Room) -> Room:
        await self.session.flush()
        await self.session.refresh(room)
        return room

    async def delete(self, room: Room) -> None:
        await self.session.delete(room)
        await self.session.flush()

    async def get_slot(self, slot_id: UUID) -> TimeSlot | None:
        result = await self.session.execute(
            select(TimeSlot).where(TimeSlot.id == slot_id)
        )
        return result.scalar_one_or_none()

    async def add_slot(self, slot: TimeSlot) -> TimeSlot:
        self.session.add(slot)
        await self.session.flush()
        await self.session.refresh(slot)
        return slot

    async def delete_slot(self, slot: TimeSlot) -> None:
        await self.session.delete(slot)
        await self.session.flush()
