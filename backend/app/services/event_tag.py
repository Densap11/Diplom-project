from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.event_tag import EventTag
from app.models.event_tag_link import EventTagLink
from app.models.user import User, UserRole
from app.schemas.event_tag import EventTagCreate


def list_event_tags(db: Session) -> list[EventTag]:
    return list(db.scalars(select(EventTag).order_by(EventTag.name)).all())


def create_event_tag(db: Session, payload: EventTagCreate) -> EventTag:
    existing_tag = db.scalar(select(EventTag).where(EventTag.name == payload.name))
    if existing_tag is not None:
        raise ValueError("Тег с таким названием уже существует")

    tag = EventTag(name=payload.name)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


def attach_tag_to_event(db: Session, event_id: int, tag_id: int, current_user: User) -> Event:
    event = db.get(Event, event_id)
    tag = db.get(EventTag, tag_id)
    if event is None:
        raise ValueError("Событие не найдено")
    if tag is None:
        raise ValueError("Тег не найден")
    if current_user.role != UserRole.admin and event.organizer_id != current_user.id:
        raise ValueError("Недостаточно прав доступа")

    existing_link = db.scalar(
        select(EventTagLink).where(
            EventTagLink.event_id == event_id,
            EventTagLink.tag_id == tag_id,
        )
    )
    if existing_link is None:
        db.add(EventTagLink(event_id=event_id, tag_id=tag_id))
        db.commit()
        db.refresh(event)
    return event


def detach_tag_from_event(db: Session, event_id: int, tag_id: int, current_user: User) -> None:
    event = db.get(Event, event_id)
    if event is None:
        raise ValueError("Событие не найдено")
    if current_user.role != UserRole.admin and event.organizer_id != current_user.id:
        raise ValueError("Недостаточно прав доступа")

    db.execute(delete(EventTagLink).where(EventTagLink.event_id == event_id, EventTagLink.tag_id == tag_id))
    db.commit()
