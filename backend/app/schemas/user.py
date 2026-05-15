from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class UserBase(BaseModel):
    full_name: str = Field(min_length=2, max_length=255, title="ФИО")
    email: EmailStr = Field(title="Email")
    faculty: str | None = Field(default=None, max_length=255, title="Факультет")
    study_group: str | None = Field(default=None, max_length=100, title="Группа")
    phone: str | None = Field(default=None, max_length=50, title="Телефон")


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=255, title="Пароль")


class UserLogin(BaseModel):
    email: EmailStr = Field(title="Email")
    password: str = Field(min_length=8, max_length=255, title="Пароль")


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(description="Идентификатор пользователя")
    role: UserRole = Field(description="Роль пользователя")
    created_at: datetime = Field(description="Дата регистрации")


class UserRoleUpdate(BaseModel):
    role: UserRole = Field(title="Новая роль пользователя")
