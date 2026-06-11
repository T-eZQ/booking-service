from uuid import uuid4

import pytest
from httpx import AsyncClient

BOOKING_DATE = "2025-04-20"


async def test_create_booking_succeeds(
    client: AsyncClient, sample_room: dict, employee_headers: dict
):
    slot_id = sample_room["slots"][0]["id"]
    resp = await client.post(
        "/api/v1/bookings",
        json={"room_id": sample_room["id"], "slot_id": slot_id, "date": BOOKING_DATE},
        headers=employee_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["date"] == BOOKING_DATE
    assert data["slot"]["id"] == slot_id
    assert data["room"]["id"] == sample_room["id"]


async def test_create_duplicate_booking_returns_409(
    client: AsyncClient, sample_room: dict, employee_headers: dict
):
    slot_id = sample_room["slots"][0]["id"]
    payload = {"room_id": sample_room["id"], "slot_id": slot_id, "date": BOOKING_DATE}

    await client.post("/api/v1/bookings", json=payload, headers=employee_headers)
    resp = await client.post("/api/v1/bookings", json=payload, headers=employee_headers)
    assert resp.status_code == 409


async def test_booking_with_wrong_room_slot_returns_404(
    client: AsyncClient, sample_room: dict, employee_headers: dict
):
    resp = await client.post(
        "/api/v1/bookings",
        json={"room_id": sample_room["id"], "slot_id": str(uuid4()), "date": BOOKING_DATE},
        headers=employee_headers,
    )
    assert resp.status_code == 404


async def test_employee_sees_only_own_bookings(
    client: AsyncClient,
    sample_room: dict,
    employee_headers: dict,
    admin_headers: dict,
):
    slot_id = sample_room["slots"][0]["id"]

    # employee creates a booking
    await client.post(
        "/api/v1/bookings",
        json={"room_id": sample_room["id"], "slot_id": slot_id, "date": BOOKING_DATE},
        headers=employee_headers,
    )

    emp_resp = await client.get("/api/v1/bookings", headers=employee_headers)
    assert len(emp_resp.json()) == 1

    admin_resp = await client.get("/api/v1/bookings", headers=admin_headers)
    assert len(admin_resp.json()) == 1


async def test_employee_cannot_access_others_booking(
    client: AsyncClient,
    sample_room: dict,
    employee_headers: dict,
    admin_headers: dict,
):
    slot_id = sample_room["slots"][0]["id"]

    # admin creates a booking using the second slot
    second_slot_id = sample_room["slots"][1]["id"]
    booking_resp = await client.post(
        "/api/v1/bookings",
        json={
            "room_id": sample_room["id"],
            "slot_id": second_slot_id,
            "date": "2025-04-21",
        },
        headers=admin_headers,
    )
    booking_id = booking_resp.json()["id"]

    # employee tries to access admin's booking
    resp = await client.get(f"/api/v1/bookings/{booking_id}", headers=employee_headers)
    assert resp.status_code == 403


async def test_employee_can_cancel_own_booking(
    client: AsyncClient, sample_room: dict, employee_headers: dict
):
    slot_id = sample_room["slots"][0]["id"]
    booking_resp = await client.post(
        "/api/v1/bookings",
        json={"room_id": sample_room["id"], "slot_id": slot_id, "date": BOOKING_DATE},
        headers=employee_headers,
    )
    booking_id = booking_resp.json()["id"]

    del_resp = await client.delete(f"/api/v1/bookings/{booking_id}", headers=employee_headers)
    assert del_resp.status_code == 204

    get_resp = await client.get(f"/api/v1/bookings/{booking_id}", headers=employee_headers)
    assert get_resp.status_code == 404


async def test_employee_cannot_cancel_others_booking(
    client: AsyncClient,
    sample_room: dict,
    employee_headers: dict,
    admin_headers: dict,
):
    slot_id = sample_room["slots"][0]["id"]
    booking_resp = await client.post(
        "/api/v1/bookings",
        json={"room_id": sample_room["id"], "slot_id": slot_id, "date": BOOKING_DATE},
        headers=admin_headers,
    )
    booking_id = booking_resp.json()["id"]

    resp = await client.delete(f"/api/v1/bookings/{booking_id}", headers=employee_headers)
    assert resp.status_code == 403


async def test_admin_can_cancel_any_booking(
    client: AsyncClient,
    sample_room: dict,
    employee_headers: dict,
    admin_headers: dict,
):
    slot_id = sample_room["slots"][0]["id"]
    booking_resp = await client.post(
        "/api/v1/bookings",
        json={"room_id": sample_room["id"], "slot_id": slot_id, "date": BOOKING_DATE},
        headers=employee_headers,
    )
    booking_id = booking_resp.json()["id"]

    resp = await client.delete(f"/api/v1/bookings/{booking_id}", headers=admin_headers)
    assert resp.status_code == 204


async def test_booked_slot_disappears_from_availability(
    client: AsyncClient,
    sample_room: dict,
    employee_headers: dict,
):
    slot_id = sample_room["slots"][0]["id"]
    await client.post(
        "/api/v1/bookings",
        json={"room_id": sample_room["id"], "slot_id": slot_id, "date": BOOKING_DATE},
        headers=employee_headers,
    )

    resp = await client.get(
        "/api/v1/rooms/availability",
        params={"date": BOOKING_DATE},
        headers=employee_headers,
    )
    room_data = next(r for r in resp.json() if r["room"]["id"] == sample_room["id"])
    available_ids = {s["id"] for s in room_data["available_slots"]}
    assert slot_id not in available_ids
