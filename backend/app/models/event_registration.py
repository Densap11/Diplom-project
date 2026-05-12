import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RegistrationStatus(str, enum.Enum):
    confirmed = "confirmed"
    cancelled = "cancelled"
    waiting_list = "waiting_list"


class EventRegistration(Base):
    __tablename__ = "event_registrations"
    __table_args__ = (
        UniqueConstraint("student_id", "event_id", name="uq_student_event_registration"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), nullable=False)
    status: Mapped[RegistrationStatus] = mapped_column(
        Enum(RegistrationStatus),
        default=RegistrationStatus.confirmed,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    student = relationship("User", back_populates="registrations")
    event = relationship("Event", back_populates="registrations")
