from uuid import UUID

from fastapi import HTTPException, status

from app.models.booking import Booking
from app.models.user import User, UserRole
from app.repositories.booking import BookingRepository
from app.repositories.room import RoomRepository
from app.schemas.booking import BookingCreate, BookingResponse


class BookingService:
    def __init__(self, booking_repo: BookingRepository, room_repo: RoomRepository) -> None:
        self.booking_repo = booking_repo
        self.room_repo = room_repo

    async def list_bookings(self, current_user: User) -> list[BookingResponse]:
        if current_user.role == UserRole.ADMIN:
            bookings = await self.booking_repo.get_all()
        else:
            bookings = await self.booking_repo.get_by_user(current_user.id)
        return [BookingResponse.model_validate(b) for b in bookings]

    async def get_booking(self, booking_id: UUID, current_user: User) -> BookingResponse:
        booking = await self.booking_repo.get_by_id(booking_id)
        if not booking:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
        if current_user.role != UserRole.ADMIN and booking.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        return BookingResponse.model_validate(booking)

    async def create_booking(self, data: BookingCreate, current_user: User) -> BookingResponse:
        room = await self.room_repo.get_by_id(data.room_id)
        if not room:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")

        slot = await self.room_repo.get_slot(data.slot_id)
        if not slot or slot.room_id != data.room_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Slot not found for this room",
            )

        existing = await self.booking_repo.get_by_slot_and_date(data.slot_id, data.date)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This slot is already booked for the selected date",
            )

        booking = Booking(
            room_id=data.room_id,
            slot_id=data.slot_id,
            user_id=current_user.id,
            date=data.date,
        )
        booking = await self.booking_repo.create(booking)
        booking = await self.booking_repo.get_by_id(booking.id)
        return BookingResponse.model_validate(booking)

    async def cancel_booking(self, booking_id: UUID, current_user: User) -> None:
        booking = await self.booking_repo.get_by_id(booking_id)
        if not booking:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
        if current_user.role != UserRole.ADMIN and booking.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        await self.booking_repo.delete(booking)
