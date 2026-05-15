from pydantic import BaseModel, EmailStr, Field


class PasswordResetRequest(BaseModel):
    email: EmailStr = Field(title="Email")


class PasswordResetConfirm(BaseModel):
    token: str = Field(min_length=16, title="Токен восстановления")
    new_password: str = Field(min_length=8, max_length=255, title="Новый пароль")


class PasswordResetRequestRead(BaseModel):
    message: str = Field(description="Сообщение о результате")
    reset_token: str | None = Field(default=None, description="Демо-токен, показывается только если разрешено настройками")
