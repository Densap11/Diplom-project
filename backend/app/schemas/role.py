from pydantic import BaseModel, ConfigDict, Field


class PermissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Идентификатор права")
    code: str = Field(description="Код права доступа")
    description: str | None = Field(description="Описание права")


class RoleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Идентификатор роли")
    name: str = Field(description="Системное имя роли")
    title: str = Field(description="Название роли")
    description: str | None = Field(description="Описание роли")
