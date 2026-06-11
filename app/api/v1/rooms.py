from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_current_user, get_room_service, require_admin
from app.models.user import User
from app.schemas.room import (
    RoomAvailability,
    RoomCreate,
    RoomResponse,
    RoomUpdate,
    TimeSlotCreate,
    TimeSlotResponse,
)
from app.services.room import RoomService

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.get("/availability", response_model=list[RoomAvailability])
async def get_availability(
    booking_date: date = Query(..., alias="date", description="Date to check (YYYY-MM-DD)"),
    service: RoomService = Depends(get_room_service),
    _: User = Depends(get_current_user),
):
    return await service.get_availability(booking_date)


@router.get("", response_model=list[RoomResponse])
async def list_rooms(
    service: RoomService = Depends(get_room_service),
    _: User = Depends(get_current_user),
):
    return await service.list_rooms()


@router.post("", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
async def create_room(
    data: RoomCreate,
    service: RoomService = Depends(get_room_service),
    _: User = Depends(require_admin),
):
    return await service.create_room(data)


@router.get("/{room_id}", response_model=RoomResponse)
async def get_room(
    room_id: UUID,
    service: RoomService = Depends(get_room_service),
    _: User = Depends(get_current_user),
):
    return await service.get_room(room_id)


@router.patch("/{room_id}", response_model=RoomResponse)
async def update_room(
    room_id: UUID,
    data: RoomUpdate,
    service: RoomService = Depends(get_room_service),
    _: User = Depends(require_admin),
):
    return await service.update_room(room_id, data)


@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_room(
    room_id: UUID,
    service: RoomService = Depends(get_room_service),
    _: User = Depends(require_admin),
):
    await service.delete_room(room_id)


@router.post("/{room_id}/slots", response_model=TimeSlotResponse, status_code=status.HTTP_201_CREATED)
async def add_slot(
    room_id: UUID,
    data: TimeSlotCreate,
    service: RoomService = Depends(get_room_service),
    _: User = Depends(require_admin),
):
    return await service.add_slot(room_id, data)


@router.delete("/{room_id}/slots/{slot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_slot(
    room_id: UUID,
    slot_id: UUID,
    service: RoomService = Depends(get_room_service),
    _: User = Depends(require_admin),
):
    await service.delete_slot(room_id, slot_id)
