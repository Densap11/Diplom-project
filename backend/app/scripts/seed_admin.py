from sqlalchemy import select

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.models.user_profile import UserProfile
from app.services.role import get_role_by_name
from app.utils.security import get_password_hash


def seed_first_admin() -> None:
    if not settings.first_admin_email or not settings.first_admin_password:
        print("FIRST_ADMIN_EMAIL и FIRST_ADMIN_PASSWORD не заданы, администратор не создан.")
        return

    db = SessionLocal()
    try:
        admin_role = get_role_by_name(db, UserRole.admin)
        user = db.scalar(select(User).where(User.email == settings.first_admin_email))
        if user is None:
            user = User(
                full_name=settings.first_admin_full_name,
                email=settings.first_admin_email,
                hashed_password=get_password_hash(settings.first_admin_password),
                role_id=admin_role.id,
                profile=UserProfile(),
            )
            db.add(user)
            print(f"Создан первый администратор: {settings.first_admin_email}")
        else:
            user.role_id = admin_role.id
            print(f"Пользователь повышен до администратора: {settings.first_admin_email}")
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed_first_admin()
