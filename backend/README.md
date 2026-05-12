# Backend

Базовый каркас backend-сервиса на FastAPI.

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
