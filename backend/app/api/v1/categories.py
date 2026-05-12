from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import require_roles
from app.models.user import User, UserRole
from app.schemas.category import CategoryCreate, CategoryRead
from app.services.category import create_category, list_categories

router = APIRouter()


@router.get(
    "",
    response_model=list[CategoryRead],
    summary="Список категорий",
    description="Возвращает все доступные категории мероприятий.",
)
def read_categories(db: Session = Depends(get_db)) -> list[CategoryRead]:
    categories = list_categories(db)
    return [CategoryRead.model_validate(category) for category in categories]


@router.post(
    "",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать категорию",
    description="Создает новую категорию. Доступно только администратору.",
)
def create_category_endpoint(
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.admin)),
) -> CategoryRead:
    try:
        category = create_category(db=db, payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return CategoryRead.model_validate(category)
