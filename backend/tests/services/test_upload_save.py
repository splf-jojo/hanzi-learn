import asyncio
from io import BytesIO
from uuid import UUID

import pytest
from fastapi import HTTPException
from PIL import Image as PILImage

from app import dependencies
from app.ocr import OCREngineError
from app.pending_uploads import PendingUploadStore
from app.schemas.images import BoundingBox, OcrBoxOut
from app.services.image_gallery import get_image_content, get_saved_image, list_saved_images
from app.services.upload_save import save_upload


def png_bytes(color=(0, 200, 100)) -> bytes:
    buffer = BytesIO()
    PILImage.new("RGB", (4, 4), color).save(buffer, format="PNG")
    return buffer.getvalue()


def unit_vector(index: int, dim: int = 512) -> list[float]:
    values = [0.0] * dim
    values[index] = 1.0
    return values


CANNED_BOXES = [
    OcrBoxOut(
        id="box_1",
        text="你好",
        confidence=0.98,
        bbox=BoundingBox(x=0.1, y=0.2, width=0.3, height=0.1),
        polygon=[[0.1, 0.2], [0.4, 0.2], [0.4, 0.3], [0.1, 0.3]],
    ),
    OcrBoxOut(
        id="box_2",
        text="世界",
        confidence=0.87,
        bbox=BoundingBox(x=0.5, y=0.6, width=0.2, height=0.1),
        polygon=[[0.5, 0.6], [0.7, 0.6], [0.7, 0.7], [0.5, 0.7]],
    ),
]


class FakeOCREngine:
    def __init__(self, boxes=None, error: Exception | None = None) -> None:
        self._boxes = boxes if boxes is not None else []
        self._error = error

    def recognize(self, data: bytes, width: int, height: int) -> list[OcrBoxOut]:
        if self._error is not None:
            raise self._error
        return list(self._boxes)


def create_pending(store: PendingUploadStore, data: bytes):
    return store.create(
        filename="upload.png",
        content_type="image/png",
        image_bytes=data,
        image_width=4,
        image_height=4,
        embedding=unit_vector(7),
    )


def test_save_upload_persists_image_and_boxes(db, monkeypatch):
    store = PendingUploadStore()
    data = png_bytes()
    upload = create_pending(store, data)
    monkeypatch.setattr(dependencies, "pending_uploads", store)
    monkeypatch.setattr(dependencies, "ocr_engine", FakeOCREngine(CANNED_BOXES))

    saved = asyncio.run(save_upload(db, upload.upload_id))

    assert saved.image_url == f"/api/images/{saved.image_id}/content"
    assert saved.filename == "upload.png"
    assert saved.content_type == "image/png"
    assert saved.image_width == 4
    assert saved.image_height == 4
    assert [box.text for box in saved.boxes] == ["你好", "世界"]
    # id боксов в ответе — UUID из базы, не box_N из парсера.
    for box in saved.boxes:
        UUID(box.id)
    assert saved.boxes[0].bbox == CANNED_BOXES[0].bbox
    assert saved.boxes[0].polygon == CANNED_BOXES[0].polygon

    # pending-загрузка удалена после сохранения
    assert store.get(upload.upload_id) is None

    # сохранённое изображение видно в галерее и отдаёт исходные байты
    fetched = asyncio.run(get_saved_image(db, saved.image_id))
    assert [box.text for box in fetched.boxes] == ["你好", "世界"]
    listing = asyncio.run(list_saved_images(db, 10, 0))
    assert saved.image_id in [image.image_id for image in listing.images]
    assert listing.has_more is False
    content = asyncio.run(get_image_content(db, saved.image_id))
    assert content.image_bytes == data
    assert content.content_type == "image/png"


def test_save_upload_unknown_id_returns_404(db, monkeypatch):
    monkeypatch.setattr(dependencies, "pending_uploads", PendingUploadStore())
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(save_upload(db, "upl_missing"))
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Pending upload was not found."


def test_save_upload_ocr_failure_returns_503_and_keeps_pending(db, monkeypatch):
    store = PendingUploadStore()
    upload = create_pending(store, png_bytes())
    monkeypatch.setattr(dependencies, "pending_uploads", store)
    monkeypatch.setattr(dependencies, "ocr_engine", FakeOCREngine(error=OCREngineError("boom")))

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(save_upload(db, upload.upload_id))
    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "boom"
    assert store.get(upload.upload_id) is not None
