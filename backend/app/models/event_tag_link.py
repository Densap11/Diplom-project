from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class EventTagLink(Base):
    __tablename__ = "event_tag_links"
    __table_args__ = (
        UniqueConstraint("event_id", "tag_id", name="uq_event_tag_link"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), nullable=False)
    tag_id: Mapped[int] = mapped_column(ForeignKey("event_tags.id"), nullable=False)

    event = relationship("Event", back_populates="tag_links")
    tag = relationship("EventTag", back_populates="events")
