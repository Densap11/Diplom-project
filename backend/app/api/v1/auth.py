from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.auth import Token
from app.schemas.password_reset import PasswordResetConfirm, PasswordResetRequest, PasswordResetRequestRead
from app.schemas.user import UserCreate, UserLogin, UserRead
from app.services.auth import (
    authenticate_user,
    create_access_token_for_user,
    create_password_reset_token,
    register_user,
    reset_password,
)

router = APIRouter()


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация пользователя",
    description="Создает нового пользователя с ролью student. Остальные роли назначает администратор.",
)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> UserRead:
    try:
        user = register_user(db=db, payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return UserRead.model_validate(user)


@router.post(
    "/login",
    response_model=Token,
    summary="Вход в систему",
    description="Проверяет email и пароль и возвращает JWT-токен доступа.",
)
def login(payload: UserLogin, db: Session = Depends(get_db)) -> Token:
    user = authenticate_user(db=db, email=payload.email, password=payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
        )
    return create_access_token_for_user(user)


@router.get(
    "/me",
    response_model=UserRead,
    summary="Текущий пользователь",
    description="Возвращает данные авторизованного пользователя по JWT-токену.",
)
def read_current_user(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)


@router.post(
    "/password-reset/request",
    response_model=PasswordResetRequestRead,
    summary="Запросить восстановление пароля",
    description="Создает токен восстановления пароля. В production токен отправляется по email.",
)
def request_password_reset(payload: PasswordResetRequest, db: Session = Depends(get_db)) -> PasswordResetRequestRead:
    return create_password_reset_token(db=db, email=payload.email)


@router.post(
    "/password-reset/confirm",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Сменить пароль по токену",
    description="Устанавливает новый пароль по действующему токену восстановления.",
)
def confirm_password_reset(payload: PasswordResetConfirm, db: Session = Depends(get_db)) -> None:
    try:
        reset_password(db=db, token=payload.token, new_password=payload.new_password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
