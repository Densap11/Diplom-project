import enum
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UserRole(str, enum.Enum):
    student = "student"
    organizer = "organizer"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    role_record = relationship("Role", back_populates="users")
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    organized_events = relationship("Event", back_populates="organizer")
    registrations = relationship("EventRegistration", back_populates="student")
    comments = relationship("EventComment", back_populates="author")
    audit_logs = relationship("AuditLog", back_populates="actor")
    password_reset_tokens = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")

    @property
    def role(self) -> UserRole:
        if self.role_record is None:
            return UserRole.student
        return UserRole(self.role_record.name)

    @property
    def faculty(self) -> str | None:
        return self.profile.faculty if self.profile is not None else None

    @property
    def study_group(self) -> str | None:
        return self.profile.study_group if self.profile is not None else None

    @property
    def phone(self) -> str | None:
        return self.profile.phone if self.profile is not None else None
