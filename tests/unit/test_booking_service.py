from datetime import date
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.models.booking import Booking
from app.models.room import Room, TimeSlot
from app.models.user import User, UserRole
from app.schemas.booking import BookingCreate
from app.services.booking import BookingService


def make_user(role: UserRole = UserRole.EMPLOYEE) -> User:
    u = User()
    u.id = uuid4()
    u.role = role
    return u


def make_room() -> Room:
    r = Room()
    r.id = uuid4()
    r.name = "Test Room"
    return r


def make_slot(room_id) -> TimeSlot:
    s = TimeSlot()
    s.id = uuid4()
    s.room_id = room_id
    s.start_time = "09:00"
    s.end_time = "11:00"
    return s


def make_booking(user_id, slot_id, room_id) -> Booking:
    b = Booking()
    b.id = uuid4()
    b.user_id = user_id
    b.slot_id = slot_id
    b.room_id = room_id
    b.date = date(2024, 6, 15)
    b.slot = make_slot(room_id)
    b.room = make_room()
    return b


@pytest.fixture
def booking_service():
    booking_repo = AsyncMock()
    room_repo = AsyncMock()
    return BookingService(booking_repo, room_repo), booking_repo, room_repo


async def test_list_bookings_employee_sees_only_own(booking_service):
    service, booking_repo, _ = booking_service
    user = make_user(UserRole.EMPLOYEE)
    booking_repo.get_by_user.return_value = []

    await service.list_bookings(user)

    booking_repo.get_by_user.assert_called_once_with(user.id)
    booking_repo.get_all.assert_not_called()


async def test_list_bookings_admin_sees_all(booking_service):
    service, booking_repo, _ = booking_service
    admin = make_user(UserRole.ADMIN)
    booking_repo.get_all.return_value = []

    await service.list_bookings(admin)

    booking_repo.get_all.assert_called_once()
    booking_repo.get_by_user.assert_not_called()


async def test_create_booking_slot_not_in_room_raises(booking_service):
    from fastapi import HTTPException

    service, booking_repo, room_repo = booking_service
    user = make_user()
    room = make_room()
    wrong_slot = make_slot(uuid4())  # slot belongs to a different room

    room_repo.get_by_id.return_value = room
    room_repo.get_slot.return_value = wrong_slot  # room_id mismatch

    data = BookingCreate(room_id=room.id, slot_id=wrong_slot.id, date=date(2024, 6, 15))

    with pytest.raises(HTTPException) as exc:
        await service.create_booking(data, user)
    assert exc.value.status_code == 404


async def test_create_booking_already_booked_raises(booking_service):
    from fastapi import HTTPException

    service, booking_repo, room_repo = booking_service
    user = make_user()
    room = make_room()
    slot = make_slot(room.id)

    room_repo.get_by_id.return_value = room
    room_repo.get_slot.return_value = slot
    booking_repo.get_by_slot_and_date.return_value = make_booking(user.id, slot.id, room.id)

    data = BookingCreate(room_id=room.id, slot_id=slot.id, date=date(2024, 6, 15))

    with pytest.raises(HTTPException) as exc:
        await service.create_booking(data, user)
    assert exc.value.status_code == 409


async def test_cancel_booking_by_owner_succeeds(booking_service):
    service, booking_repo, _ = booking_service
    user = make_user()
    booking = make_booking(user.id, uuid4(), uuid4())
    booking_repo.get_by_id.return_value = booking

    await service.cancel_booking(booking.id, user)

    booking_repo.delete.assert_called_once_with(booking)


async def test_cancel_booking_by_other_employee_raises(booking_service):
    from fastapi import HTTPException

    service, booking_repo, _ = booking_service
    owner = make_user()
    other = make_user()
    booking = make_booking(owner.id, uuid4(), uuid4())
    booking_repo.get_by_id.return_value = booking

    with pytest.raises(HTTPException) as exc:
        await service.cancel_booking(booking.id, other)
    assert exc.value.status_code == 403


async def test_cancel_booking_by_admin_succeeds(booking_service):
    service, booking_repo, _ = booking_service
    owner = make_user()
    admin = make_user(UserRole.ADMIN)
    booking = make_booking(owner.id, uuid4(), uuid4())
    booking_repo.get_by_id.return_value = booking

    await service.cancel_booking(booking.id, admin)

    booking_repo.delete.assert_called_once_with(booking)


async def test_get_booking_not_found_raises(booking_service):
    from fastapi import HTTPException

    service, booking_repo, _ = booking_service
    booking_repo.get_by_id.return_value = None
    user = make_user()

    with pytest.raises(HTTPException) as exc:
        await service.get_booking(uuid4(), user)
    assert exc.value.status_code == 404
