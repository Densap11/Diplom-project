from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.event import EventFormat, EventStatus
from app.schemas.event_tag import EventTagRead


class EventBase(BaseModel):
    title: str = Field(min_length=3, max_length=255, title="Название")
    short_description: str = Field(min_length=10, max_length=500, title="Краткое описание")
    full_description: str = Field(min_length=20, title="Полное описание")
    event_date: datetime = Field(title="Дата и время проведения")
    location: str = Field(min_length=3, max_length=255, title="Место проведения")
    contacts: str = Field(min_length=3, max_length=255, title="Контакты организатора")
    format: EventFormat = Field(default=EventFormat.offline, title="Формат проведения")
    category_id: int = Field(title="ID категории")
    is_unlimited: bool = Field(default=False, title="Без ограничения мест")
    max_participants: int | None = Field(default=None, ge=1, title="Максимум участников")
    status: EventStatus = Field(default=EventStatus.draft, title="Статус события")

    @model_validator(mode="after")
    def validate_participants(self) -> "EventBase":
        if self.is_unlimited and self.max_participants is not None:
            raise ValueError("Для безлимитного события нельзя указывать лимит участников")
        if not self.is_unlimited and self.max_participants is None:
            raise ValueError("Для события с ограничением мест нужно указать max_participants")
        return self


class EventCreate(EventBase):
    pass


class EventStatusUpdate(BaseModel):
    status: EventStatus = Field(title="Новый статус события")


class EventRead(EventBase):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Идентификатор события")
    organizer_id: int = Field(description="Идентификатор организатора")
    image_url: str | None = Field(default=None, description="Ссылка на обложку события")
    tags: list[EventTagRead] = Field(default_factory=list, description="Теги события")
    confirmed_participants: int = Field(default=0, description="Количество подтвержденных участников")
    remaining_places: int | None = Field(default=None, description="Количество оставшихся мест")
    created_at: datetime = Field(description="Дата создания")
    updated_at: datetime = Field(description="Дата последнего обновления")
