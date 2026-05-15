from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import require_permissions
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryRead
from app.services.audit import create_audit_log
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
    current_user: User = Depends(require_permissions("categories:manage")),
) -> CategoryRead:
    try:
        category = create_category(db=db, payload=payload)
        create_audit_log(
            db,
            action="category.create",
            entity_type="category",
            entity_id=category.id,
            actor=current_user,
            details=f"Создана категория: {category.name}",
        )
        db.commit()
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return CategoryRead.model_validate(category)
