import re
from uuid import UUID

from pydantic import BaseModel, field_validator


class TimeSlotCreate(BaseModel):
    start_time: str
    end_time: str

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        if not re.match(r"^\d{2}:\d{2}$", v):
            raise ValueError("Time must be in HH:MM format")
        h, m = map(int, v.split(":"))
        if not (0 <= h <= 23 and 0 <= m <= 59):
            raise ValueError("Invalid time value")
        return v


class TimeSlotResponse(BaseModel):
    id: UUID
    start_time: str
    end_time: str

    model_config = {"from_attributes": True}


class RoomCreate(BaseModel):
    name: str
    description: str | None = None
    capacity: int | None = None
    slots: list[TimeSlotCreate] = []


class RoomUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    capacity: int | None = None


class RoomResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    capacity: int | None
    slots: list[TimeSlotResponse] = []

    model_config = {"from_attributes": True}


class RoomAvailability(BaseModel):
    room: RoomResponse
    available_slots: list[TimeSlotResponse]
