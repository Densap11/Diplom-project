from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user, require_permissions
from app.models.user import User
from app.schemas.event import EventRead
from app.schemas.event_tag import EventTagCreate, EventTagRead
from app.services.event_tag import attach_tag_to_event, create_event_tag, detach_tag_from_event, list_event_tags

router = APIRouter()


@router.get(
    "/tags",
    response_model=list[EventTagRead],
    summary="Список тегов событий",
    description="Возвращает теги, которыми можно дополнительно размечать мероприятия.",
)
def read_event_tags(db: Session = Depends(get_db)) -> list[EventTagRead]:
    tags = list_event_tags(db)
    return [EventTagRead.model_validate(tag) for tag in tags]


@router.post(
    "/tags",
    response_model=EventTagRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать тег события",
    description="Создает новый тег. Доступно организатору или администратору.",
)
def create_event_tag_endpoint(
    payload: EventTagCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("events:manage-own")),
) -> EventTagRead:
    try:
        tag = create_event_tag(db=db, payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return EventTagRead.model_validate(tag)


@router.post(
    "/{event_id}/tags/{tag_id}",
    response_model=EventRead,
    summary="Добавить тег к событию",
    description="Связывает событие с тегом. Доступно владельцу события или администратору.",
)
def attach_event_tag_endpoint(
    event_id: int,
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EventRead:
    try:
        event = attach_tag_to_event(db=db, event_id=event_id, tag_id=tag_id, current_user=current_user)
    except ValueError as exc:
        message = str(exc)
        if message in ("Событие не найдено", "Тег не найден"):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message) from exc
        if message == "Недостаточно прав доступа":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message) from exc
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message) from exc
    return EventRead.model_validate(event)


@router.delete(
    "/{event_id}/tags/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Убрать тег с события",
    description="Удаляет связь события и тега.",
)
def detach_event_tag_endpoint(
    event_id: int,
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    try:
        detach_tag_from_event(db=db, event_id=event_id, tag_id=tag_id, current_user=current_user)
    except ValueError as exc:
        message = str(exc)
        if message == "Событие не найдено":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message) from exc
        if message == "Недостаточно прав доступа":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message) from exc
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
