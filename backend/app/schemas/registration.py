from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.event_registration import RegistrationStatus
from app.models.user import UserRole


class EventRegistrationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Идентификатор записи")
    student_id: int = Field(description="Идентификатор студента")
    event_id: int = Field(description="Идентификатор события")
    status: RegistrationStatus = Field(description="Статус записи")
    created_at: datetime = Field(description="Дата и время записи")


class EventParticipantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Идентификатор участника")
    full_name: str = Field(description="ФИО участника")
    email: str = Field(description="Email участника")
    faculty: str | None = Field(description="Факультет")
    study_group: str | None = Field(description="Группа")
    phone: str | None = Field(description="Телефон")
    role: UserRole = Field(description="Роль пользователя")
