from pydantic import BaseModel, ConfigDict, Field


class CategoryCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=100,
        title="Название категории",
        description="Например: Волонтерство, Концерты, Секции, Подкасты",
    )


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Уникальный идентификатор категории")
    name: str = Field(description="Название категории мероприятия")
