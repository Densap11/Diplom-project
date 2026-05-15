from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.event import Event, EventStatus
from app.models.event_registration import EventRegistration, RegistrationStatus
from app.models.user import User, UserRole


def register_for_event(db: Session, event_id: int, student: User) -> EventRegistration:
    event = db.scalar(select(Event).where(Event.id == event_id).with_for_update())
    if event is None or event.status != EventStatus.published:
        raise ValueError("Событие не найдено")

    existing_registration = db.scalar(
        select(EventRegistration).where(
            EventRegistration.event_id == event_id,
            EventRegistration.student_id == student.id,
        )
    )

    if not event.is_unlimited:
        confirmed_count = db.scalar(
            select(func.count(EventRegistration.id)).where(
                EventRegistration.event_id == event_id,
                EventRegistration.status == RegistrationStatus.confirmed,
            )
        )
        if confirmed_count is not None and event.max_participants is not None:
            if confirmed_count >= event.max_participants:
                raise ValueError("Свободных мест больше нет")

    if existing_registration is not None:
        if existing_registration.status == RegistrationStatus.cancelled:
            existing_registration.status = RegistrationStatus.confirmed
            db.commit()
            db.refresh(existing_registration)
            return existing_registration
        raise ValueError("Пользователь уже записан на это событие")

    registration = EventRegistration(
        student_id=student.id,
        event_id=event_id,
        status=RegistrationStatus.confirmed,
    )
    db.add(registration)
    db.commit()
    db.refresh(registration)
    return registration


def cancel_registration(db: Session, event_id: int, student: User) -> EventRegistration:
    registration = db.scalar(
        select(EventRegistration).where(
            EventRegistration.event_id == event_id,
            EventRegistration.student_id == student.id,
        )
    )
    if registration is None:
        raise ValueError("Запись на событие не найдена")
    if registration.status == RegistrationStatus.cancelled:
        raise ValueError("Запись уже отменена")

    registration.status = RegistrationStatus.cancelled
    db.commit()
    db.refresh(registration)
    return registration


def list_event_participants(db: Session, event_id: int, current_user: User) -> list[User]:
    event = db.get(Event, event_id)
    if event is None:
        raise ValueError("Событие не найдено")

    if current_user.role != UserRole.admin and event.organizer_id != current_user.id:
        raise ValueError("Недостаточно прав доступа")

    query = (
        select(User)
        .join(EventRegistration, EventRegistration.student_id == User.id)
        .where(
            EventRegistration.event_id == event_id,
            EventRegistration.status == RegistrationStatus.confirmed,
        )
        .order_by(User.full_name)
    )
    return list(db.scalars(query).all())
