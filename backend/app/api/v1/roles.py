from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import require_permissions
from app.models.user import User
from app.schemas.role import RoleRead
from app.services.role import list_roles

router = APIRouter()


@router.get(
    "",
    response_model=list[RoleRead],
    summary="Список ролей",
    description="Возвращает доступные роли RBAC. Доступно администратору.",
)
def read_roles(
    db: Session = Depends(get_db),
    _: User = Depends(require_permissions("users:manage")),
) -> list[RoleRead]:
    roles = list_roles(db)
    return [RoleRead.model_validate(role) for role in roles]
