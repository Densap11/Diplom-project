from datetime import datetime, timedelta, timezone
from hashlib import sha256
from secrets import token_urlsafe

from jose import jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User, UserRole
from app.models.user_profile import UserProfile
from app.models.password_reset_token import PasswordResetToken
from app.schemas.auth import Token
from app.schemas.password_reset import PasswordResetRequestRead
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


def hash_reset_token(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


def create_password_reset_token(db: Session, email: str) -> PasswordResetRequestRead:
    user = db.scalar(select(User).where(User.email == email))
    generic_message = "Если пользователь найден, инструкция по восстановлению будет отправлена."
    if user is None:
        return PasswordResetRequestRead(message=generic_message)

    raw_token = token_urlsafe(32)
    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=hash_reset_token(raw_token),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
    )
    db.add(reset_token)
    db.commit()

    # В production здесь подключается email-провайдер. Для демо токен можно открыть через env.
    return PasswordResetRequestRead(
        message=generic_message,
        reset_token=raw_token if settings.expose_demo_reset_token else None,
    )


def reset_password(db: Session, token: str, new_password: str) -> None:
    token_hash = hash_reset_token(token)
    reset_token = db.scalar(select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash))
    now = datetime.now(timezone.utc)
    if reset_token is None or reset_token.used_at is not None or reset_token.expires_at < now:
        raise ValueError("Токен восстановления недействителен или истек")

    reset_token.user.hashed_password = get_password_hash(new_password)
    reset_token.used_at = now
    db.commit()
