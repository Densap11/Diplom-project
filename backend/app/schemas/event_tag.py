from pydantic import BaseModel, ConfigDict, Field


class EventTagCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80, title="Название тега")


class EventTagRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Идентификатор тега")
    name: str = Field(description="Название тега")
