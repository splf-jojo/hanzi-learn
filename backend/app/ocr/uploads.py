from __future__ import annotations

from io import BytesIO

from fastapi import HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError


ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


async def read_image_upload(file: UploadFile, max_bytes: int, max_pixels: int) -> tuple[bytes, int, int]:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only JPEG, PNG, and WEBP images are supported.",
        )

    data = await file.read()
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image file is empty.")
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image is larger than {max_bytes // 1024 // 1024} MB.",
        )

    try:
        with Image.open(BytesIO(data)) as image:
            image.load()
            width, height = image.size
    except UnidentifiedImageError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image file.") from exc

    if width * height > max_pixels:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Image dimensions are too large.",
        )

    return data, width, height
