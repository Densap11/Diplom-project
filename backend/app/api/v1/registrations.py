from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user, require_roles
from app.models.user import User, UserRole
from app.schemas.registration import EventParticipantRead, EventRegistrationRead
from app.services.registration import (
    cancel_registration,
    list_event_participants,
    register_for_event,
)

router = APIRouter()


@router.post(
    "/events/{event_id}/register",
    response_model=EventRegistrationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Записаться на событие",
    description="Создает запись студента на выбранное опубликованное событие.",
)
def register_for_event_endpoint(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.student, UserRole.admin)),
) -> EventRegistrationRead:
    try:
        registration = register_for_event(db=db, event_id=event_id, student=current_user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return EventRegistrationRead.model_validate(registration)


@router.delete(
    "/events/{event_id}/register",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Отменить запись",
    description="Отменяет запись текущего пользователя на событие.",
)
def cancel_registration_endpoint(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.student, UserRole.admin)),
) -> Response:
    try:
        cancel_registration(db=db, event_id=event_id, student=current_user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/events/{event_id}/participants",
    response_model=list[EventParticipantRead],
    summary="Список участников события",
    description="Возвращает подтвержденных участников выбранного события.",
)
def read_event_participants(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[EventParticipantRead]:
    try:
        participants = list_event_participants(db=db, event_id=event_id, current_user=current_user)
    except ValueError as exc:
        message = str(exc)
        if message == "Событие не найдено":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message) from exc
        if message == "Недостаточно прав доступа":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message) from exc
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message) from exc

    return [EventParticipantRead.model_validate(participant) for participant in participants]
