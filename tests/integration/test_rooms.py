import pytest
from httpx import AsyncClient


async def test_list_rooms_returns_empty_initially(client: AsyncClient, employee_headers: dict):
    resp = await client.get("/api/v1/rooms", headers=employee_headers)
    assert resp.status_code == 200
    assert resp.json() == []


async def test_create_room_as_admin_succeeds(client: AsyncClient, admin_headers: dict):
    resp = await client.post(
        "/api/v1/rooms",
        json={"name": "Alpha", "capacity": 8},
        headers=admin_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Alpha"
    assert data["capacity"] == 8
    assert data["slots"] == []


async def test_create_room_as_employee_returns_403(client: AsyncClient, employee_headers: dict):
    resp = await client.post(
        "/api/v1/rooms",
        json={"name": "Forbidden Room"},
        headers=employee_headers,
    )
    assert resp.status_code == 403


async def test_create_room_with_duplicate_name_returns_409(
    client: AsyncClient, admin_headers: dict
):
    payload = {"name": "Unique Room"}
    await client.post("/api/v1/rooms", json=payload, headers=admin_headers)
    resp = await client.post("/api/v1/rooms", json=payload, headers=admin_headers)
    assert resp.status_code == 409


async def test_get_room_by_id(client: AsyncClient, admin_headers: dict, employee_headers: dict):
    create_resp = await client.post(
        "/api/v1/rooms", json={"name": "Beta"}, headers=admin_headers
    )
    room_id = create_resp.json()["id"]

    resp = await client.get(f"/api/v1/rooms/{room_id}", headers=employee_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == room_id


async def test_get_nonexistent_room_returns_404(
    client: AsyncClient, employee_headers: dict
):
    from uuid import uuid4

    resp = await client.get(f"/api/v1/rooms/{uuid4()}", headers=employee_headers)
    assert resp.status_code == 404


async def test_add_slot_to_room(client: AsyncClient, sample_room: dict, admin_headers: dict):
    room_id = sample_room["id"]
    resp = await client.post(
        f"/api/v1/rooms/{room_id}/slots",
        json={"start_time": "15:00", "end_time": "17:00"},
        headers=admin_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["start_time"] == "15:00"
    assert data["end_time"] == "17:00"


async def test_add_slot_invalid_time_order_returns_422(
    client: AsyncClient, sample_room: dict, admin_headers: dict
):
    resp = await client.post(
        f"/api/v1/rooms/{sample_room['id']}/slots",
        json={"start_time": "17:00", "end_time": "09:00"},
        headers=admin_headers,
    )
    assert resp.status_code == 422


async def test_delete_slot(client: AsyncClient, sample_room: dict, admin_headers: dict):
    room_id = sample_room["id"]
    slot_id = sample_room["slots"][0]["id"]

    resp = await client.delete(
        f"/api/v1/rooms/{room_id}/slots/{slot_id}", headers=admin_headers
    )
    assert resp.status_code == 204


async def test_update_room(client: AsyncClient, sample_room: dict, admin_headers: dict):
    room_id = sample_room["id"]
    resp = await client.patch(
        f"/api/v1/rooms/{room_id}",
        json={"name": "Renamed Room", "capacity": 12},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Renamed Room"
    assert resp.json()["capacity"] == 12


async def test_delete_room(client: AsyncClient, admin_headers: dict, employee_headers: dict):
    create_resp = await client.post(
        "/api/v1/rooms", json={"name": "To Delete"}, headers=admin_headers
    )
    room_id = create_resp.json()["id"]

    del_resp = await client.delete(f"/api/v1/rooms/{room_id}", headers=admin_headers)
    assert del_resp.status_code == 204

    get_resp = await client.get(f"/api/v1/rooms/{room_id}", headers=employee_headers)
    assert get_resp.status_code == 404


async def test_availability_shows_free_slots(
    client: AsyncClient,
    sample_room: dict,
    employee_headers: dict,
):
    resp = await client.get(
        "/api/v1/rooms/availability",
        params={"date": "2025-03-10"},
        headers=employee_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["room"]["id"] == sample_room["id"]
    assert len(data[0]["available_slots"]) == 2
