from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)

    slots: Mapped[list["TimeSlot"]] = relationship(
        back_populates="room",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    bookings: Mapped[list["Booking"]] = relationship(back_populates="room")  # noqa: F821


class TimeSlot(Base):
    __tablename__ = "time_slots"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    room_id: Mapped[UUID] = mapped_column(
        ForeignKey("rooms.id", ondelete="CASCADE"),
        index=True,
    )
    start_time: Mapped[str] = mapped_column(String(5))  # "HH:MM"
    end_time: Mapped[str] = mapped_column(String(5))    # "HH:MM"

    room: Mapped["Room"] = relationship(back_populates="slots")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="slot")  # noqa: F821
