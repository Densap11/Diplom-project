import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.event_registration import RegistrationStatus


class EventFormat(str, enum.Enum):
    offline = "offline"
    online = "online"
    mixed = "mixed"


class EventStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    archived = "archived"


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    short_description: Mapped[str] = mapped_column(String(500), nullable=False)
    full_description: Mapped[str] = mapped_column(Text, nullable=False)
    event_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    contacts: Mapped[str] = mapped_column(String(255), nullable=False)
    image_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    max_participants: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_unlimited: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[EventStatus] = mapped_column(
        Enum(EventStatus),
        default=EventStatus.draft,
        nullable=False,
    )
    format: Mapped[EventFormat] = mapped_column(
        Enum(EventFormat),
        default=EventFormat.offline,
        nullable=False,
    )
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False)
    organizer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    category = relationship("Category", back_populates="events")
    organizer = relationship("User", back_populates="organized_events")
    registrations = relationship("EventRegistration", back_populates="event")

    @property
    def image_url(self) -> str | None:
        if not self.image_path:
            return None
        return f"/media/{self.image_path}"

    @property
    def confirmed_participants(self) -> int:
        return sum(1 for registration in self.registrations if registration.status == RegistrationStatus.confirmed)

    @property
    def remaining_places(self) -> int | None:
        if self.is_unlimited or self.max_participants is None:
            return None
        return max(self.max_participants - self.confirmed_participants, 0)
