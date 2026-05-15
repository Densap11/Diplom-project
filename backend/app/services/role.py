from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.permission import Permission
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.user import UserRole


DEFAULT_ROLES = {
    UserRole.student: "Студент",
    UserRole.organizer: "Организатор",
    UserRole.admin: "Администратор",
}

DEFAULT_PERMISSIONS = {
    "events:read": "Просмотр опубликованных мероприятий",
    "events:create": "Создание мероприятий",
    "events:manage-own": "Управление своими мероприятиями",
    "events:manage-all": "Управление всеми мероприятиями",
    "registrations:create": "Запись на мероприятия",
    "users:manage": "Управление пользователями и ролями",
    "categories:manage": "Управление категориями",
    "comments:create": "Создание комментариев",
}

ROLE_PERMISSION_CODES = {
    UserRole.student: ["events:read", "registrations:create", "comments:create"],
    UserRole.organizer: ["events:read", "events:create", "events:manage-own", "comments:create"],
    UserRole.admin: list(DEFAULT_PERMISSIONS),
}


def ensure_default_roles(db: Session) -> None:
    for role_name, title in DEFAULT_ROLES.items():
        role = db.scalar(select(Role).where(Role.name == role_name.value))
        if role is None:
            role = Role(name=role_name.value, title=title)
            db.add(role)

    for code, description in DEFAULT_PERMISSIONS.items():
        permission = db.scalar(select(Permission).where(Permission.code == code))
        if permission is None:
            permission = Permission(code=code, description=description)
            db.add(permission)

    db.flush()

    for role_name, permission_codes in ROLE_PERMISSION_CODES.items():
        role = get_role_by_name(db, role_name)
        for code in permission_codes:
            permission = db.scalar(select(Permission).where(Permission.code == code))
            exists = db.scalar(
                select(RolePermission).where(
                    RolePermission.role_id == role.id,
                    RolePermission.permission_id == permission.id,
                )
            )
            if exists is None:
                db.add(RolePermission(role_id=role.id, permission_id=permission.id))

    db.commit()


def get_role_by_name(db: Session, role: UserRole) -> Role:
    role_record = db.scalar(select(Role).where(Role.name == role.value))
    if role_record is None:
        ensure_default_roles(db)
        role_record = db.scalar(select(Role).where(Role.name == role.value))
    if role_record is None:
        raise ValueError("Роль не найдена")
    return role_record


def list_roles(db: Session) -> list[Role]:
    ensure_default_roles(db)
    return list(db.scalars(select(Role).order_by(Role.id)).all())
