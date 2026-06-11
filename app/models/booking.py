from datetime import UTC, date, datetime
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (UniqueConstraint("slot_id", "date", name="uq_slot_date"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    room_id: Mapped[UUID] = mapped_column(ForeignKey("rooms.id"), index=True)
    slot_id: Mapped[UUID] = mapped_column(ForeignKey("time_slots.id"), index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    room: Mapped["Room"] = relationship(back_populates="bookings")  # noqa: F821
    slot: Mapped["TimeSlot"] = relationship(back_populates="bookings")  # noqa: F821
    user: Mapped["User"] = relationship(back_populates="bookings")  # noqa: F821
