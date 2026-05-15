from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import require_permissions
from app.models.user import User
from app.models.event import EventFormat
from app.schemas.event import EventCreate, EventRead, EventStatusUpdate
from app.services.event import (
    create_event,
    delete_event,
    get_manageable_events,
    get_published_event_by_id,
    list_published_events,
    update_event,
    update_event_status,
)
from app.utils.files import save_event_image

router = APIRouter()


@router.get(
    "",
    response_model=list[EventRead],
    summary="Список опубликованных событий",
    description="Возвращает общую доску опубликованных мероприятий.",
)
def read_events(
    search: str | None = Query(None, min_length=1),
    category_id: int | None = Query(None, ge=1),
    format: EventFormat | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> list[EventRead]:
    events = list_published_events(
        db,
        search=search,
        category_id=category_id,
        format_value=format,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )
    return [EventRead.model_validate(event) for event in events]


@router.get(
    "/manage",
    response_model=list[EventRead],
    summary="События для управления",
    description="Возвращает события организатора или все события для администратора.",
)
def read_manageable_events(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("events:manage-own")),
) -> list[EventRead]:
    events = get_manageable_events(db=db, current_user=current_user)
    return [EventRead.model_validate(event) for event in events]


@router.get(
    "/{event_id}",
    response_model=EventRead,
    summary="Карточка события",
    description="Возвращает подробную информацию об одном опубликованном событии.",
)
def read_event(event_id: int, db: Session = Depends(get_db)) -> EventRead:
    event = get_published_event_by_id(db=db, event_id=event_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Событие не найдено")
    return EventRead.model_validate(event)


@router.post(
    "",
    response_model=EventRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать событие",
    description="Создает новое событие от имени организатора или администратора. Поддерживает загрузку обложки.",
)
def create_event_endpoint(
    title: str = Form(..., description="Название события"),
    short_description: str = Form(..., description="Краткое описание"),
    full_description: str = Form(..., description="Полное описание"),
    event_date: datetime = Form(..., description="Дата и время проведения"),
    location: str = Form(..., description="Место проведения"),
    contacts: str = Form(..., description="Контакты организатора"),
    format: str = Form(..., description="Формат: offline, online или mixed"),
    category_id: int = Form(..., description="Идентификатор категории"),
    is_unlimited: bool = Form(False, description="Есть ли ограничение по местам"),
    max_participants: int | None = Form(None, description="Лимит участников"),
    status_value: str = Form(..., alias="status", description="Статус: draft или published"),
    image: UploadFile | None = File(None, description="Обложка события"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("events:create")),
) -> EventRead:
    try:
        payload = EventCreate(
            title=title,
            short_description=short_description,
            full_description=full_description,
            event_date=event_date,
            location=location,
            contacts=contacts,
            format=format,
            category_id=category_id,
            is_unlimited=is_unlimited,
            max_participants=max_participants,
            status=status_value,
        )
        image_path = save_event_image(image)
        event = create_event(db=db, payload=payload, organizer=current_user, image_path=image_path)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return EventRead.model_validate(event)


@router.put(
    "/{event_id}",
    response_model=EventRead,
    summary="Редактировать событие",
    description="Обновляет данные события. Доступно организатору-владельцу и администратору.",
)
def update_event_endpoint(
    event_id: int,
    title: str = Form(...),
    short_description: str = Form(...),
    full_description: str = Form(...),
    event_date: datetime = Form(...),
    location: str = Form(...),
    contacts: str = Form(...),
    format: str = Form(...),
    category_id: int = Form(...),
    is_unlimited: bool = Form(False),
    max_participants: int | None = Form(None),
    status_value: str = Form(..., alias="status"),
    image: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("events:manage-own")),
) -> EventRead:
    try:
        payload = EventCreate(
            title=title,
            short_description=short_description,
            full_description=full_description,
            event_date=event_date,
            location=location,
            contacts=contacts,
            format=format,
            category_id=category_id,
            is_unlimited=is_unlimited,
            max_participants=max_participants,
            status=status_value,
        )
        image_path = save_event_image(image) if image is not None and image.filename else None
        event = update_event(
            db=db,
            event_id=event_id,
            payload=payload,
            current_user=current_user,
            image_path=image_path,
        )
    except ValueError as exc:
        message = str(exc)
        code = status.HTTP_404_NOT_FOUND if message == "Событие не найдено" else status.HTTP_400_BAD_REQUEST
        if message == "Недостаточно прав доступа":
            code = status.HTTP_403_FORBIDDEN
        raise HTTPException(status_code=code, detail=message) from exc
    return EventRead.model_validate(event)


@router.patch(
    "/{event_id}/status",
    response_model=EventRead,
    summary="Изменить статус события",
    description="Позволяет опубликовать, архивировать или вернуть событие в черновик.",
)
def update_event_status_endpoint(
    event_id: int,
    payload: EventStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("events:manage-own")),
) -> EventRead:
    try:
        event = update_event_status(
            db=db,
            event_id=event_id,
            status=payload.status,
            current_user=current_user,
        )
    except ValueError as exc:
        message = str(exc)
        code = status.HTTP_404_NOT_FOUND if message == "Событие не найдено" else status.HTTP_400_BAD_REQUEST
        if message == "Недостаточно прав доступа":
            code = status.HTTP_403_FORBIDDEN
        raise HTTPException(status_code=code, detail=message) from exc
    return EventRead.model_validate(event)


@router.delete(
    "/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить событие",
    description="Удаляет событие. Доступно организатору-владельцу и администратору.",
)
def delete_event_endpoint(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("events:manage-own")),
) -> None:
    try:
        delete_event(db=db, event_id=event_id, current_user=current_user)
    except ValueError as exc:
        message = str(exc)
        code = status.HTTP_404_NOT_FOUND if message == "Событие не найдено" else status.HTTP_400_BAD_REQUEST
        if message == "Недостаточно прав доступа":
            code = status.HTTP_403_FORBIDDEN
        raise HTTPException(status_code=code, detail=message) from exc
