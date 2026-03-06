"""
File service — handles saving and deleting uploaded files.
Abstracts file storage so swapping from local disk to S3 later
requires changing only this file.
"""
import uuid
from pathlib import Path

import aiofiles
from fastapi import UploadFile

from app.config import get_settings
from app.core.exceptions import FileTooLargeError
from app.core.logger.logger import logger

settings = get_settings()

_UPLOAD_ROOT = Path(settings.file_upload_dir)
_MAX_BYTES = settings.max_upload_size_mb * 1024 * 1024


class FileService:
    async def save(self, file: UploadFile, subfolder: str = "") -> str:
        """
        Persist an uploaded file to disk and return its relative URL path.
        The URL format is /uploads/<subfolder>/<uuid>_<original_name>.
        """
        destination = _UPLOAD_ROOT / subfolder
        destination.mkdir(parents=True, exist_ok=True)

        # Read content into memory to check size before writing
        content = await file.read()
        if len(content) > _MAX_BYTES:
            raise FileTooLargeError(settings.max_upload_size_mb)

        safe_name = f"{uuid.uuid4().hex}_{Path(file.filename or 'file').name}"
        file_path = destination / safe_name

        async with aiofiles.open(file_path, "wb") as out:
            await out.write(content)

        relative_url = f"/uploads/{subfolder}/{safe_name}".replace("//", "/")
        logger.debug("Saved file {} → {}", file.filename, relative_url)
        return relative_url

    async def delete(self, file_url: str) -> None:
        """Remove a file from disk given its relative URL."""
        file_path = _UPLOAD_ROOT / file_url.removeprefix("/uploads/")
        if file_path.exists():
            file_path.unlink()
            logger.debug("Deleted file {}", file_path)
        else:
            logger.warning("Attempted to delete non-existent file: {}", file_path)
