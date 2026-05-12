from pydantic import BaseModel, Field


class HealthCheckRead(BaseModel):
    status: str = Field(description="Текущий статус сервиса")
    service: str = Field(description="Имя проверяемого сервиса")
