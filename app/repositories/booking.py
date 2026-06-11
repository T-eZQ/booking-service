from datetime import date
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.booking import Booking


class BookingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, booking_id: UUID) -> Booking | None:
        result = await self.session.execute(
            select(Booking)
            .options(selectinload(Booking.slot), selectinload(Booking.room))
            .where(Booking.id == booking_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user(self, user_id: UUID) -> list[Booking]:
        result = await self.session.execute(
            select(Booking)
            .options(selectinload(Booking.slot), selectinload(Booking.room))
            .where(Booking.user_id == user_id)
            .order_by(Booking.date.desc(), Booking.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_all(self) -> list[Booking]:
        result = await self.session.execute(
            select(Booking)
            .options(
                selectinload(Booking.slot),
                selectinload(Booking.room),
                selectinload(Booking.user),
            )
            .order_by(Booking.date.desc(), Booking.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_slot_and_date(self, slot_id: UUID, booking_date: date) -> Booking | None:
        result = await self.session.execute(
            select(Booking).where(
                and_(Booking.slot_id == slot_id, Booking.date == booking_date)
            )
        )
        return result.scalar_one_or_none()

    async def get_booked_slot_ids(self, room_id: UUID, booking_date: date) -> set[UUID]:
        result = await self.session.execute(
            select(Booking.slot_id).where(
                and_(Booking.room_id == room_id, Booking.date == booking_date)
            )
        )
        return set(result.scalars().all())

    async def create(self, booking: Booking) -> Booking:
        self.session.add(booking)
        await self.session.flush()
        await self.session.refresh(booking)
        return booking

    async def delete(self, booking: Booking) -> None:
        await self.session.delete(booking)
        await self.session.flush()
