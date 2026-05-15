from datetime import datetime, timedelta, timezone

from jose import jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User, UserRole
from app.models.user_profile import UserProfile
from app.schemas.auth import Token
from app.schemas.user import UserCreate
from app.services.role import get_role_by_name
from app.utils.security import get_password_hash, verify_password


def register_user(db: Session, payload: UserCreate) -> User:
    existing_user = db.scalar(select(User).where(User.email == payload.email))
    if existing_user is not None:
        raise ValueError("Пользователь с таким email уже существует")

    role = get_role_by_name(db, UserRole.student)
    user = User(
        full_name=payload.full_name,
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        role_id=role.id,
        profile=UserProfile(
            faculty=payload.faculty,
            study_group=payload.study_group,
            phone=payload.phone,
        ),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def create_access_token_for_user(user: User) -> Token:
    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return Token(access_token=token)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
