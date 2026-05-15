from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.event import Event, EventStatus
from app.models.event_comment import EventComment
from app.models.event_registration import EventRegistration
from app.models.event_tag_link import EventTagLink
from app.models.user import User
from app.schemas.event import EventCreate


def list_published_events(db: Session) -> list[Event]:
    query = select(Event).where(Event.status == EventStatus.published).order_by(Event.event_date)
    return list(db.scalars(query).all())


def get_published_event_by_id(db: Session, event_id: int) -> Event | None:
    query = select(Event).where(Event.id == event_id, Event.status == EventStatus.published)
    return db.scalar(query)


def create_event(
    db: Session,
    payload: EventCreate,
    organizer: User,
    image_path: str | None = None,
) -> Event:
    category = db.get(Category, payload.category_id)
    if category is None:
        raise ValueError("Категория не найдена")

    event = Event(
        title=payload.title,
        short_description=payload.short_description,
        full_description=payload.full_description,
        event_date=payload.event_date,
        location=payload.location,
        contacts=payload.contacts,
        image_path=image_path,
        max_participants=payload.max_participants,
        is_unlimited=payload.is_unlimited,
        status=payload.status,
        format=payload.format,
        category_id=payload.category_id,
        organizer_id=organizer.id,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def get_manageable_events(db: Session, current_user: User) -> list[Event]:
    query = select(Event)
    if current_user.role != "admin":
        query = query.where(Event.organizer_id == current_user.id)
    query = query.order_by(Event.created_at.desc())
    return list(db.scalars(query).all())


def get_event_for_management(db: Session, event_id: int, current_user: User) -> Event:
    event = db.get(Event, event_id)
    if event is None:
        raise ValueError("Событие не найдено")
    if current_user.role != "admin" and event.organizer_id != current_user.id:
        raise ValueError("Недостаточно прав доступа")
    return event


def update_event(
    db: Session,
    event_id: int,
    payload: EventCreate,
    current_user: User,
    image_path: str | None = None,
) -> Event:
    category = db.get(Category, payload.category_id)
    if category is None:
        raise ValueError("Категория не найдена")

    event = get_event_for_management(db=db, event_id=event_id, current_user=current_user)
    event.title = payload.title
    event.short_description = payload.short_description
    event.full_description = payload.full_description
    event.event_date = payload.event_date
    event.location = payload.location
    event.contacts = payload.contacts
    event.max_participants = payload.max_participants
    event.is_unlimited = payload.is_unlimited
    event.status = payload.status
    event.format = payload.format
    event.category_id = payload.category_id
    if image_path is not None:
        event.image_path = image_path

    db.commit()
    db.refresh(event)
    return event


def update_event_status(
    db: Session,
    event_id: int,
    status: EventStatus,
    current_user: User,
) -> Event:
    event = get_event_for_management(db=db, event_id=event_id, current_user=current_user)
    event.status = status
    db.commit()
    db.refresh(event)
    return event


def delete_event(db: Session, event_id: int, current_user: User) -> None:
    event = get_event_for_management(db=db, event_id=event_id, current_user=current_user)
    db.execute(delete(EventComment).where(EventComment.event_id == event.id))
    db.execute(delete(EventRegistration).where(EventRegistration.event_id == event.id))
    db.execute(delete(EventTagLink).where(EventTagLink.event_id == event.id))
    db.delete(event)
    db.commit()
