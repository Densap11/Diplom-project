from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class EventTag(Base):
    __tablename__ = "event_tags"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)

    events = relationship("EventTagLink", back_populates="tag", cascade="all, delete-orphan")
