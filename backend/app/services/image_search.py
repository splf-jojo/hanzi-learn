from __future__ import annotations

import asyncio
import logging

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from .. import dependencies
from ..clip_service import ImageEmbeddingError
from ..ocr import read_image_upload
from ..repositories import images as images_repository
from ..schemas.images import ImageMatch, ImageSearchResponse, image_content_url


logger = logging.getLogger(__name__)


async def search_uploaded_image(db: Session, image: UploadFile) -> ImageSearchResponse:
    logger.info(
        "image.search.start filename=%s content_type=%s",
        image.filename,
        image.content_type,
    )
    data, width, height = await read_image_upload(
        image,
        max_bytes=dependencies.settings.max_image_bytes,
        max_pixels=dependencies.settings.max_image_pixels,
    )
    logger.info(
        "image.search.upload_validated filename=%s bytes=%s image_width=%s image_height=%s",
        image.filename,
        len(data),
        width,
        height,
    )

    try:
        embedding = await asyncio.to_thread(dependencies.clip_embedder.embed_image, data)
        logger.info("image.search.embedding_finish filename=%s dimensions=%s", image.filename, len(embedding))
        matches = await asyncio.to_thread(_search_matches, db, embedding)
        log_image_matches(image.filename, matches)
    except ImageEmbeddingError as exc:
        logger.exception("image.search.embedding_failed filename=%s", image.filename)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("image.search.failed filename=%s", image.filename)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    upload = dependencies.pending_uploads.create(
        filename=image.filename,
        content_type=image.content_type or "application/octet-stream",
        image_bytes=data,
        image_width=width,
        image_height=height,
        embedding=embedding,
    )
    logger.info(
        "image.search.finish upload_id=%s image_width=%s image_height=%s matches=%s",
        upload.upload_id,
        width,
        height,
        len(matches),
    )
    return ImageSearchResponse(
        upload_id=upload.upload_id,
        image_width=width,
        image_height=height,
        matches=matches,
    )


def _search_matches(db: Session, embedding: list[float]) -> list[ImageMatch]:
    results = images_repository.search_similar(db, embedding, 5)
    return [
        ImageMatch(
            image_id=str(image.id),
            image_url=image_content_url(str(image.id)),
            filename=image.filename,
            image_width=image.image_width,
            image_height=image.image_height,
            similarity=similarity,
        )
        for image, similarity in results
    ]


def log_image_matches(filename: str | None, matches: list[ImageMatch]) -> None:
    if not matches:
        logger.info("image.search.matches_empty filename=%s", filename)
        return

    logger.info(
        "image.search.matches_found filename=%s count=%s ids=%s",
        filename,
        len(matches),
        [match.image_id for match in matches],
    )
    for rank, match in enumerate(matches, start=1):
        logger.info(
            "image.search.match rank=%s image_id=%s similarity=%.4f filename=%s image_width=%s image_height=%s",
            rank,
            match.image_id,
            match.similarity,
            match.filename,
            match.image_width,
            match.image_height,
        )
