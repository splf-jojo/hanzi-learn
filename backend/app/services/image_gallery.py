from __future__ import annotations

import asyncio
from dataclasses import dataclass
import logging
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..models import Image, OcrBox
from ..repositories import images as images_repository
from ..schemas.images import (
    BoundingBox,
    GalleryImage,
    ImageListResponse,
    OcrBoxOut,
    SavedImageResponse,
    image_content_url,
)


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class StoredImageContent:
    image_bytes: bytes
    content_type: str
    filename: str | None


def parse_uuid(value: str) -> UUID | None:
    try:
        return UUID(value)
    except ValueError:
        return None


def box_to_out(box: OcrBox) -> OcrBoxOut:
    return OcrBoxOut(
        id=str(box.id),
        text=box.text,
        confidence=float(box.confidence),
        bbox=BoundingBox(**box.bbox),
        polygon=box.polygon,
    )


def image_to_saved_response(image: Image) -> SavedImageResponse:
    image_id = str(image.id)
    return SavedImageResponse(
        image_id=image_id,
        image_width=image.image_width,
        image_height=image.image_height,
        image_url=image_content_url(image_id),
        filename=image.filename,
        content_type=image.content_type,
        boxes=[box_to_out(box) for box in image.boxes],
    )


async def list_saved_images(db: Session, limit: int, offset: int) -> ImageListResponse:
    try:
        images, has_more = await asyncio.to_thread(_list_images, db, limit, offset)
    except Exception as exc:
        logger.exception("image.list.failed limit=%s offset=%s", limit, offset)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    logger.info("image.list.finish limit=%s offset=%s count=%s has_more=%s", limit, offset, len(images), has_more)
    return ImageListResponse(images=images, limit=limit, offset=offset, has_more=has_more)


def _list_images(db: Session, limit: int, offset: int) -> tuple[list[GalleryImage], bool]:
    rows, has_more = images_repository.list_images(db, limit, offset)
    images = [
        GalleryImage(
            image_id=str(image.id),
            image_url=image_content_url(str(image.id)),
            filename=image.filename,
            image_width=image.image_width,
            image_height=image.image_height,
            created_at=image.created_at,
        )
        for image in rows
    ]
    return images, has_more


async def get_saved_image(db: Session, image_id: str) -> SavedImageResponse:
    try:
        image = await asyncio.to_thread(_get_image, db, image_id)
    except Exception as exc:
        logger.exception("image.get.failed image_id=%s", image_id)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    if image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved image was not found.")
    logger.info("image.get.finish image_id=%s boxes=%s", image.image_id, len(image.boxes))
    return image


def _get_image(db: Session, image_id: str) -> SavedImageResponse | None:
    parsed_id = parse_uuid(image_id)
    if parsed_id is None:
        return None
    image = images_repository.get_image(db, parsed_id)
    if image is None:
        return None
    return image_to_saved_response(image)


async def get_image_content(db: Session, image_id: str) -> StoredImageContent:
    try:
        content = await asyncio.to_thread(_get_content, db, image_id)
    except Exception as exc:
        logger.exception("image.content.failed image_id=%s", image_id)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    if content is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved image was not found.")
    return content


def _get_content(db: Session, image_id: str) -> StoredImageContent | None:
    parsed_id = parse_uuid(image_id)
    if parsed_id is None:
        return None
    row = images_repository.get_content(db, parsed_id)
    if row is None:
        return None
    image_bytes, content_type, filename = row
    return StoredImageContent(image_bytes=image_bytes, content_type=content_type, filename=filename)
