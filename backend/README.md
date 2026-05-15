# Backend

[![CI](https://github.com/Densap11/Diplom-project/actions/workflows/ci.yml/badge.svg)](https://github.com/Densap11/Diplom-project/actions/workflows/ci.yml)
[![Docker Smoke](https://github.com/Densap11/Diplom-project/actions/workflows/docker-smoke.yml/badge.svg)](https://github.com/Densap11/Diplom-project/actions/workflows/docker-smoke.yml)

Backend-сервис на FastAPI для агрегации внеучебной активности университета.

## Структура базы данных

Проект использует PostgreSQL, SQLAlchemy 2.0 и Alembic. Схема нормализована до 11 таблиц:

1. `roles` — справочник ролей пользователей: студент, организатор, администратор.
2. `permissions` — справочник атомарных прав доступа для дальнейшего развития RBAC.
3. `role_permissions` — many-to-many связь ролей и прав.
4. `users` — учетные записи пользователей, email, пароль и ссылка на роль.
5. `user_profiles` — дополнительные данные пользователя: факультет, группа, телефон.
6. `categories` — категории мероприятий.
7. `events` — основная сущность проекта: внеучебные мероприятия.
8. `event_registrations` — записи студентов на мероприятия.
9. `event_tags` — дополнительные теги для гибкой разметки мероприятий.
10. `event_tag_links` — many-to-many связь мероприятий и тегов.
11. `event_comments` — комментарии пользователей к опубликованным мероприятиям.
12. `audit_logs` — журнал административных действий.
13. `password_reset_tokens` — одноразовые токены восстановления пароля.

Основные связи:

- `roles` 1:N `users`;
- `roles` M:N `permissions` через `role_permissions`;
- `users` 1:1 `user_profiles`;
- `users` 1:N `events` как организатор;
- `categories` 1:N `events`;
- `users` M:N `events` через `event_registrations`;
- `events` M:N `event_tags` через `event_tag_links`;
- `users` 1:N `event_comments`;
- `events` 1:N `event_comments`.
- `users` 1:N `audit_logs`;
- `users` 1:N `password_reset_tokens`.

## Production-подготовка

Перед размещением на сервере обязательно задайте в `.env`:

- `SECRET_KEY` — длинная случайная строка, не `change-me`;
- `CORS_ORIGINS` — точные домены frontend, например `https://example.com`;
- `POSTGRES_PASSWORD` — надежный пароль базы данных;
- `FIRST_ADMIN_EMAIL`, `FIRST_ADMIN_PASSWORD`, `FIRST_ADMIN_FULL_NAME` — данные первого администратора.

Docker Compose включает PostgreSQL, backend, frontend и one-shot backup-сервис.

Запуск:

```bash
docker compose up -d --build
docker compose exec backend python -m app.scripts.seed_admin
```

Резервная копия PostgreSQL:

```bash
docker compose --profile tools run --rm backup
```

Для HTTPS используйте внешний reverse proxy. Пример конфигурации лежит в `../deploy/nginx.https.example.conf`.

## Безопасность и устойчивость

- Доступ к защищенным endpoint проверяется через `permissions` и `role_permissions`.
- Публичная регистрация всегда создает пользователя с ролью `student`.
- Загрузка обложек ограничена по MIME-типу, расширению и размеру.
- Запись на мероприятие блокирует строку события на время проверки лимита мест.
- Административные изменения пишутся в `audit_logs`.
- Восстановление пароля реализовано через одноразовые токены; отправка email подключается через внешний почтовый сервис.

## Быстрый старт

1. Скопировать `.env.example` в `.env`
2. Установить зависимости:

```bash
pip install -r requirements.txt
```

3. Запустить сервер:

```bash
uvicorn app.main:app --reload
```

4. Открыть документацию:

- `http://localhost:8000/docs`
- `http://localhost:8000/redoc`
