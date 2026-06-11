from datetime import date
from uuid import UUID

from fastapi import HTTPException, status

from app.models.room import Room, TimeSlot
from app.repositories.booking import BookingRepository
from app.repositories.room import RoomRepository
from app.schemas.room import (
    RoomAvailability,
    RoomCreate,
    RoomResponse,
    RoomUpdate,
    TimeSlotCreate,
    TimeSlotResponse,
)


class RoomService:
    def __init__(self, room_repo: RoomRepository, booking_repo: BookingRepository) -> None:
        self.room_repo = room_repo
        self.booking_repo = booking_repo

    async def list_rooms(self) -> list[RoomResponse]:
        rooms = await self.room_repo.get_all()
        return [RoomResponse.model_validate(r) for r in rooms]

    async def get_room(self, room_id: UUID) -> RoomResponse:
        room = await self.room_repo.get_by_id(room_id)
        if not room:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
        return RoomResponse.model_validate(room)

    async def create_room(self, data: RoomCreate) -> RoomResponse:
        if await self.room_repo.get_by_name(data.name):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Room with this name already exists",
            )
        room = Room(name=data.name, description=data.description, capacity=data.capacity)
        room = await self.room_repo.create(room)

        slot_responses: list[TimeSlotResponse] = []
        for slot_data in data.slots:
            if slot_data.start_time >= slot_data.end_time:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"start_time must be before end_time for slot {slot_data.start_time}-{slot_data.end_time}",
                )
            slot = await self.room_repo.add_slot(
                TimeSlot(room_id=room.id, start_time=slot_data.start_time, end_time=slot_data.end_time)
            )
            slot_responses.append(TimeSlotResponse.model_validate(slot))

        # Build response from in-memory objects to avoid SQLAlchemy identity-map
        # caching the empty slots collection that was populated during refresh().
        return RoomResponse.model_validate(room).model_copy(update={"slots": slot_responses})

    async def update_room(self, room_id: UUID, data: RoomUpdate) -> RoomResponse:
        room = await self.room_repo.get_by_id(room_id)
        if not room:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
        if data.name is not None and data.name != room.name:
            if await self.room_repo.get_by_name(data.name):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Room with this name already exists",
                )
            room.name = data.name
        if data.description is not None:
            room.description = data.description
        if data.capacity is not None:
            room.capacity = data.capacity
        room = await self.room_repo.update(room)
        return RoomResponse.model_validate(room)

    async def delete_room(self, room_id: UUID) -> None:
        room = await self.room_repo.get_by_id(room_id)
        if not room:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
        await self.room_repo.delete(room)

    async def add_slot(self, room_id: UUID, data: TimeSlotCreate) -> TimeSlotResponse:
        room = await self.room_repo.get_by_id(room_id)
        if not room:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
        if data.start_time >= data.end_time:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="start_time must be before end_time",
            )
        slot = TimeSlot(room_id=room_id, start_time=data.start_time, end_time=data.end_time)
        slot = await self.room_repo.add_slot(slot)
        return TimeSlotResponse.model_validate(slot)

    async def delete_slot(self, room_id: UUID, slot_id: UUID) -> None:
        slot = await self.room_repo.get_slot(slot_id)
        if not slot or slot.room_id != room_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Slot not found")
        await self.room_repo.delete_slot(slot)

    async def get_availability(self, booking_date: date) -> list[RoomAvailability]:
        rooms = await self.room_repo.get_all()
        result = []
        for room in rooms:
            booked_ids = await self.booking_repo.get_booked_slot_ids(room.id, booking_date)
            available_slots = [
                TimeSlotResponse.model_validate(s)
                for s in sorted(room.slots, key=lambda s: s.start_time)
                if s.id not in booked_ids
            ]
            result.append(
                RoomAvailability(
                    room=RoomResponse.model_validate(room),
                    available_slots=available_slots,
                )
            )
        return result
