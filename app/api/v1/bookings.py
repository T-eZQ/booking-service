from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.deps import get_booking_service, get_current_user
from app.models.user import User
from app.schemas.booking import BookingCreate, BookingResponse
from app.services.booking import BookingService

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.get("", response_model=list[BookingResponse])
async def list_bookings(
    service: BookingService = Depends(get_booking_service),
    current_user: User = Depends(get_current_user),
):
    return await service.list_bookings(current_user)


@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(
    data: BookingCreate,
    service: BookingService = Depends(get_booking_service),
    current_user: User = Depends(get_current_user),
):
    return await service.create_booking(data, current_user)


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: UUID,
    service: BookingService = Depends(get_booking_service),
    current_user: User = Depends(get_current_user),
):
    return await service.get_booking(booking_id, current_user)


@router.delete("/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_booking(
    booking_id: UUID,
    service: BookingService = Depends(get_booking_service),
    current_user: User = Depends(get_current_user),
):
    await service.cancel_booking(booking_id, current_user)
