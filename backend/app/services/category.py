from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.schemas.category import CategoryCreate


def list_categories(db: Session) -> list[Category]:
    return list(db.scalars(select(Category).order_by(Category.name)).all())


def create_category(db: Session, payload: CategoryCreate) -> Category:
    existing_category = db.scalar(select(Category).where(Category.name == payload.name))
    if existing_category is not None:
        raise ValueError("Категория с таким названием уже существует")

    category = Category(name=payload.name)
    db.add(category)
    db.commit()
    db.refresh(category)
    return category
