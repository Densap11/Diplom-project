from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import Category, Event, EventStatus, User, UserRole, UserProfile
from app.services.role import get_role_by_name
from app.utils.security import get_password_hash


@pytest.fixture()
def db_session_factory():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=Session)
    Base.metadata.create_all(bind=engine)
    try:
        yield TestingSessionLocal
    finally:
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session_factory) -> TestClient:

    def override_get_db():
        db = db_session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def register(client: TestClient, email: str, password: str = "password123", role: str | None = None) -> dict:
    payload = {
        "full_name": "Тестовый Пользователь",
        "email": email,
        "password": password,
        "faculty": "ИТ",
        "study_group": "ИТ-01",
    }
    if role is not None:
        payload["role"] = role
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def login(client: TestClient, email: str, password: str = "password123") -> str:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def create_user(db: Session, email: str, role: UserRole) -> User:
    role_record = get_role_by_name(db, role)
    user = User(
        full_name=email,
        email=email,
        hashed_password=get_password_hash("password123"),
        role_id=role_record.id,
        profile=UserProfile(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_public_registration_always_creates_student(client: TestClient) -> None:
    user = register(client, "student@example.com", role="admin")

    assert user["role"] == "student"


def test_permissions_protect_admin_routes(client: TestClient, db_session_factory) -> None:
    register(client, "student@example.com")
    student_token = login(client, "student@example.com")

    forbidden_response = client.post(
        "/api/v1/categories",
        json={"name": "Волонтерство"},
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert forbidden_response.status_code == 403

    with db_session_factory() as db:
        create_user(db, "admin@example.com", UserRole.admin)

    admin_token = login(client, "admin@example.com")
    created_response = client.post(
        "/api/v1/categories",
        json={"name": "Волонтерство"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert created_response.status_code == 201, created_response.text


def test_event_capacity_limit_is_enforced(client: TestClient, db_session_factory) -> None:
    with db_session_factory() as db:
        organizer = create_user(db, "organizer@example.com", UserRole.organizer)
        student_one = create_user(db, "student1@example.com", UserRole.student)
        student_two = create_user(db, "student2@example.com", UserRole.student)
        category = Category(name="Спорт")
        db.add(category)
        db.flush()
        event = Event(
            title="Турнир по шахматам",
            short_description="Университетский шахматный турнир",
            full_description="Подробное описание университетского шахматного турнира",
            event_date=datetime.now(timezone.utc) + timedelta(days=1),
            location="Аудитория 101",
            contacts="organizer@example.com",
            max_participants=1,
            is_unlimited=False,
            status=EventStatus.published,
            category_id=category.id,
            organizer_id=organizer.id,
        )
        db.add(event)
        db.commit()
        event_id = event.id
        assert student_one.id
        assert student_two.id

    first_token = login(client, "student1@example.com")
    second_token = login(client, "student2@example.com")

    first_response = client.post(
        f"/api/v1/events/{event_id}/register",
        headers={"Authorization": f"Bearer {first_token}"},
    )
    second_response = client.post(
        f"/api/v1/events/{event_id}/register",
        headers={"Authorization": f"Bearer {second_token}"},
    )

    assert first_response.status_code == 201, first_response.text
    assert second_response.status_code == 400
    assert second_response.json()["detail"] == "Свободных мест больше нет"
