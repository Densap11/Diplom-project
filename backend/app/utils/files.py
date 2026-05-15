from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import settings


def save_event_image(file: UploadFile | None) -> str | None:
    if file is None or not file.filename:
        return None

    if file.content_type not in settings.allowed_image_type_set:
        raise ValueError("Поддерживаются только изображения JPEG, PNG или WebP")

    suffix = Path(file.filename).suffix.lower() or ".jpg"
    if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise ValueError("Недопустимое расширение файла изображения")

    content = file.file.read(settings.max_upload_size_bytes + 1)
    if len(content) > settings.max_upload_size_bytes:
        raise ValueError("Размер изображения превышает допустимый лимит")

    filename = f"{uuid4().hex}{suffix}"
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    destination = upload_dir / filename

    with destination.open("wb") as buffer:
        buffer.write(content)

    return filename
