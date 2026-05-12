from fastapi import APIRouter

from app.schemas.health import HealthCheckRead

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthCheckRead,
    summary="Проверка доступности сервиса",
    description="Возвращает простой ответ, подтверждающий, что backend работает.",
)
async def health_check() -> HealthCheckRead:
    return HealthCheckRead(status="ok", service="backend")
