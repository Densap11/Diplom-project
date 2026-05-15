from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Идентификатор записи журнала")
    actor_id: int | None = Field(description="Идентификатор пользователя, выполнившего действие")
    action: str = Field(description="Действие")
    entity_type: str = Field(description="Тип сущности")
    entity_id: int | None = Field(description="Идентификатор сущности")
    details: str | None = Field(description="Дополнительные детали")
    created_at: datetime = Field(description="Дата действия")
