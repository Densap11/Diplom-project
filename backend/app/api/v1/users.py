from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user, require_permissions
from app.models.user import User
from app.schemas.event import EventRead
from app.schemas.registration import EventRegistrationRead
from app.schemas.user import UserRead, UserRoleUpdate
from app.services.user import delete_user, list_my_events, list_my_registrations, list_users, update_user_role

router = APIRouter()


@router.get(
    "/me/events",
    response_model=list[EventRead],
    summary="Мои события",
    description="Возвращает события, созданные текущим организатором.",
)
def read_my_events(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[EventRead]:
    events = list_my_events(db=db, current_user=current_user)
    return [EventRead.model_validate(event) for event in events]


@router.get(
    "/me/registrations",
    response_model=list[EventRegistrationRead],
    summary="Мои записи",
    description="Возвращает список событий, на которые записан текущий пользователь.",
)
def read_my_registrations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[EventRegistrationRead]:
    registrations = list_my_registrations(db=db, current_user=current_user)
    return [EventRegistrationRead.model_validate(registration) for registration in registrations]


@router.get(
    "",
    response_model=list[UserRead],
    summary="Список пользователей",
    description="Возвращает список всех пользователей. Доступно только администратору.",
)
def read_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("users:manage")),
) -> list[UserRead]:
    users = list_users(db=db)
    return [UserRead.model_validate(user) for user in users]


@router.patch(
    "/{user_id}/role",
    response_model=UserRead,
    summary="Изменить роль пользователя",
    description="Обновляет роль пользователя. Доступно только администратору.",
)
def update_user_role_endpoint(
    user_id: int,
    payload: UserRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("users:manage")),
) -> UserRead:
    try:
        user = update_user_role(db=db, user_id=user_id, role=payload.role, current_user=current_user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return UserRead.model_validate(user)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить пользователя",
    description="Удаляет пользователя вместе с его регистрациями и событиями. Доступно только администратору.",
)
def delete_user_endpoint(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions("users:manage")),
) -> Response:
    try:
        delete_user(db=db, user_id=user_id, current_user=current_user)
    except ValueError as exc:
        message = str(exc)
        code = status.HTTP_404_NOT_FOUND if message == "Пользователь не найден" else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=message) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)
