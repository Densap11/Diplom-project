from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.api.router import api_router
from app.core.config import settings


def create_application() -> FastAPI:
    openapi_tags = [
        {"name": "auth", "description": "Аутентификация, регистрация и работа с текущим пользователем."},
        {"name": "categories", "description": "Категории внеучебных мероприятий."},
        {"name": "roles", "description": "Роли и базовая RBAC-структура доступа."},
        {"name": "events", "description": "Публикация, просмотр и карточки мероприятий."},
        {"name": "event-tags", "description": "Дополнительная разметка мероприятий тегами."},
        {"name": "event-comments", "description": "Комментарии пользователей к мероприятиям."},
        {"name": "registrations", "description": "Запись студентов на мероприятия и список участников."},
        {"name": "users", "description": "Данные личного кабинета пользователя."},
        {"name": "health", "description": "Проверка доступности backend-сервиса."},
    ]
    application = FastAPI(
        title=settings.project_name,
        version=settings.app_version,
        summary="API сервиса агрегации внеучебной деятельности университета",
        description=(
            "Документация REST API для сервиса, в котором организаторы публикуют события, "
            "а студенты просматривают общую доску мероприятий и записываются на участие."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        openapi_tags=openapi_tags,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    upload_path = Path(settings.upload_dir)
    upload_path.mkdir(parents=True, exist_ok=True)
    application.mount(settings.media_prefix, StaticFiles(directory=upload_path), name="media")
    application.include_router(api_router, prefix=settings.api_v1_prefix)
    return application


app = create_application()
