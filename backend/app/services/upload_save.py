from __future__ import annotations

import asyncio
import logging

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from .. import dependencies
from ..ocr import OCREngineError
from ..pending_uploads import PendingUpload
from ..repositories import images as images_repository
from ..schemas.images import OcrBoxOut, SavedImageResponse
from .image_gallery import image_to_saved_response


logger = logging.getLogger(__name__)


async def save_upload(db: Session, upload_id: str) -> SavedImageResponse:
    upload = dependencies.pending_uploads.get(upload_id)
    if upload is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pending upload was not found.")

    logger.info("upload.save.start upload_id=%s filename=%s", upload.upload_id, upload.filename)
    try:
        boxes = await asyncio.to_thread(
            dependencies.ocr_engine.recognize,
            upload.image_bytes,
            upload.image_width,
            upload.image_height,
        )
        logger.info(
            "upload.save.ocr_finish upload_id=%s boxes=%s texts=%s",
            upload_id,
            len(boxes),
            [box.text for box in boxes],
        )
        saved = await asyncio.to_thread(_save_image, db, upload, boxes)
        logger.info("upload.save.database_finish upload_id=%s image_id=%s", upload_id, saved.image_id)
    except OCREngineError as exc:
        logger.exception("upload.save.ocr_failed upload_id=%s", upload_id)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("upload.save.failed upload_id=%s", upload_id)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    dependencies.pending_uploads.remove(upload_id)
    logger.info("upload.save.finish upload_id=%s image_id=%s boxes=%s", upload_id, saved.image_id, len(saved.boxes))
    return saved


def _save_image(db: Session, upload: PendingUpload, boxes: list[OcrBoxOut]) -> SavedImageResponse:
    image = images_repository.save_image(
        db,
        filename=upload.filename or "",
        content_type=upload.content_type,
        image_bytes=upload.image_bytes,
        image_width=upload.image_width,
        image_height=upload.image_height,
        embedding=upload.embedding,
        boxes=[
            {
                "text": box.text,
                "confidence": box.confidence,
                "bbox": box.bbox.model_dump(),
                "polygon": box.polygon,
            }
            for box in boxes
        ],
    )
    response = image_to_saved_response(image)
    db.commit()
    return response
