from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user, require_roles
from app.models.user import User, UserRole
from app.schemas.event_comment import EventCommentCreate, EventCommentRead
from app.services.event_comment import create_event_comment, delete_event_comment, list_event_comments

router = APIRouter()


@router.get(
    "/{event_id}/comments",
    response_model=list[EventCommentRead],
    summary="Комментарии события",
    description="Возвращает комментарии к опубликованному мероприятию.",
)
def read_event_comments(event_id: int, db: Session = Depends(get_db)) -> list[EventCommentRead]:
    try:
        comments = list_event_comments(db=db, event_id=event_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return [EventCommentRead.model_validate(comment) for comment in comments]


@router.post(
    "/{event_id}/comments",
    response_model=EventCommentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Добавить комментарий",
    description="Добавляет комментарий к опубликованному мероприятию.",
)
def create_event_comment_endpoint(
    event_id: int,
    payload: EventCommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.student, UserRole.organizer, UserRole.admin)),
) -> EventCommentRead:
    try:
        comment = create_event_comment(db=db, event_id=event_id, payload=payload, author=current_user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return EventCommentRead.model_validate(comment)


@router.delete(
    "/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить комментарий",
    description="Удаляет свой комментарий или любой комментарий для администратора.",
)
def delete_event_comment_endpoint(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    try:
        delete_event_comment(db=db, comment_id=comment_id, current_user=current_user)
    except ValueError as exc:
        message = str(exc)
        if message == "Комментарий не найден":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message) from exc
        if message == "Недостаточно прав доступа":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message) from exc
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)
