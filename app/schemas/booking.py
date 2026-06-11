from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel

from app.schemas.room import TimeSlotResponse


class RoomBrief(BaseModel):
    id: UUID
    name: str

    model_config = {"from_attributes": True}


class BookingCreate(BaseModel):
    room_id: UUID
    slot_id: UUID
    date: date


class BookingResponse(BaseModel):
    id: UUID
    user_id: UUID
    date: date
    created_at: datetime
    room: RoomBrief | None = None
    slot: TimeSlotResponse | None = None

    model_config = {"from_attributes": True}
