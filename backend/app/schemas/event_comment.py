from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EventCommentCreate(BaseModel):
    text: str = Field(min_length=2, max_length=2000, title="Текст комментария")


class EventCommentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Идентификатор комментария")
    event_id: int = Field(description="Идентификатор события")
    author_id: int = Field(description="Идентификатор автора")
    text: str = Field(description="Текст комментария")
    created_at: datetime = Field(description="Дата создания")
