from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.event_registration import EventRegistration
from app.models.user import User, UserRole


def list_my_events(db: Session, current_user: User) -> list[Event]:
    if current_user.role not in (UserRole.organizer, UserRole.admin):
        return []

    query = select(Event).where(Event.organizer_id == current_user.id).order_by(Event.event_date)
    return list(db.scalars(query).all())


def list_my_registrations(db: Session, current_user: User) -> list[EventRegistration]:
    query = (
        select(EventRegistration)
        .where(EventRegistration.student_id == current_user.id)
        .order_by(EventRegistration.created_at.desc())
    )
    return list(db.scalars(query).all())


def list_users(db: Session) -> list[User]:
    query = select(User).order_by(User.created_at.desc())
    return list(db.scalars(query).all())


def update_user_role(db: Session, user_id: int, role: UserRole) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise ValueError("Пользователь не найден")

    user.role = role
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int, current_user: User) -> None:
    user = db.get(User, user_id)
    if user is None:
        raise ValueError("Пользователь не найден")
    if user.id == current_user.id:
        raise ValueError("Нельзя удалить собственный аккаунт")

    owned_event_ids = list(
        db.scalars(select(Event.id).where(Event.organizer_id == user.id)).all()
    )

    if owned_event_ids:
        db.execute(delete(EventRegistration).where(EventRegistration.event_id.in_(owned_event_ids)))
        db.execute(delete(Event).where(Event.id.in_(owned_event_ids)))

    db.execute(delete(EventRegistration).where(EventRegistration.student_id == user.id))
    db.delete(user)
    db.commit()
