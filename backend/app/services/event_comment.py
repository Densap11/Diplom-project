from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.event import Event, EventStatus
from app.models.event_comment import EventComment
from app.models.user import User, UserRole
from app.schemas.event_comment import EventCommentCreate


def list_event_comments(db: Session, event_id: int) -> list[EventComment]:
    event = db.get(Event, event_id)
    if event is None or event.status != EventStatus.published:
        raise ValueError("Событие не найдено")

    query = select(EventComment).where(EventComment.event_id == event_id).order_by(EventComment.created_at.desc())
    return list(db.scalars(query).all())


def create_event_comment(
    db: Session,
    event_id: int,
    payload: EventCommentCreate,
    author: User,
) -> EventComment:
    event = db.get(Event, event_id)
    if event is None or event.status != EventStatus.published:
        raise ValueError("Событие не найдено")

    comment = EventComment(event_id=event_id, author_id=author.id, text=payload.text)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def delete_event_comment(db: Session, comment_id: int, current_user: User) -> None:
    comment = db.get(EventComment, comment_id)
    if comment is None:
        raise ValueError("Комментарий не найден")

    if current_user.role != UserRole.admin and comment.author_id != current_user.id:
        raise ValueError("Недостаточно прав доступа")

    db.delete(comment)
    db.commit()
