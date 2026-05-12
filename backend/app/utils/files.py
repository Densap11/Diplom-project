from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import settings


def save_event_image(file: UploadFile | None) -> str | None:
    if file is None or not file.filename:
        return None

    suffix = Path(file.filename).suffix.lower() or ".jpg"
    filename = f"{uuid4().hex}{suffix}"
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    destination = upload_dir / filename

    with destination.open("wb") as buffer:
        buffer.write(file.file.read())

    return filename
