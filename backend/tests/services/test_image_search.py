import asyncio
from io import BytesIO

import pytest
from fastapi import HTTPException
from PIL import Image as PILImage
from sqlalchemy import text
from starlette.datastructures import Headers, UploadFile

from app import dependencies
from app.models import Image
from app.pending_uploads import PendingUploadStore
from app.services.image_search import search_uploaded_image


def png_bytes(color=(255, 0, 0)) -> bytes:
    buffer = BytesIO()
    PILImage.new("RGB", (4, 4), color).save(buffer, format="PNG")
    return buffer.getvalue()


def make_upload(data: bytes, filename="query.png", content_type="image/png") -> UploadFile:
    return UploadFile(
        BytesIO(data),
        filename=filename,
        headers=Headers({"content-type": content_type}),
    )


def unit_vector(index: int, dim: int = 512) -> list[float]:
    values = [0.0] * dim
    values[index] = 1.0
    return values


class FakeEmbedder:
    def __init__(self, embedding: list[float]) -> None:
        self._embedding = embedding

    def embed_image(self, image_bytes: bytes) -> list[float]:
        return list(self._embedding)


def add_image(db, *, filename: str, embedding: list[float]):
    image = Image(
        filename=filename,
        content_type="image/png",
        image_bytes=png_bytes(),
        image_width=4,
        image_height=4,
        embedding=embedding,
    )
    db.add(image)
    db.flush()
    return image


def test_search_orders_matches_by_similarity(db, monkeypatch):
    # ivfflat-индекс, построенный по пустой таблице, может терять строки —
    # для проверки порядка нужен точный скан.
    db.execute(text("SET LOCAL enable_indexscan = off"))
    query = unit_vector(0)
    identical = add_image(db, filename="identical.png", embedding=unit_vector(0))
    halfway = unit_vector(0)
    halfway[1] = 1.0  # 45 градусов к запросу
    diagonal = add_image(db, filename="diagonal.png", embedding=halfway)
    orthogonal = add_image(db, filename="orthogonal.png", embedding=unit_vector(1))

    store = PendingUploadStore()
    monkeypatch.setattr(dependencies, "pending_uploads", store)
    monkeypatch.setattr(dependencies, "clip_embedder", FakeEmbedder(query))

    response = asyncio.run(search_uploaded_image(db, make_upload(png_bytes())))

    assert response.image_width == 4
    assert response.image_height == 4
    assert [match.image_id for match in response.matches] == [
        str(identical.id),
        str(diagonal.id),
        str(orthogonal.id),
    ]
    similarities = [match.similarity for match in response.matches]
    assert similarities == sorted(similarities, reverse=True)
    assert similarities[0] == pytest.approx(1.0, abs=1e-6)
    assert similarities[2] == pytest.approx(0.0, abs=1e-6)
    assert response.matches[0].image_url == f"/api/images/{identical.id}/content"

    assert response.upload_id.startswith("upl_")
    pending = store.get(response.upload_id)
    assert pending is not None
    assert pending.embedding == query
    assert pending.image_width == 4
    assert pending.filename == "query.png"


def test_search_with_no_saved_images_returns_empty_matches(db, monkeypatch):
    monkeypatch.setattr(dependencies, "pending_uploads", PendingUploadStore())
    monkeypatch.setattr(dependencies, "clip_embedder", FakeEmbedder(unit_vector(3)))

    response = asyncio.run(search_uploaded_image(db, make_upload(png_bytes())))
    assert response.matches == []
    assert response.upload_id.startswith("upl_")


def test_search_rejects_unsupported_content_type(db):
    upload = make_upload(b"whatever", filename="note.txt", content_type="text/plain")
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(search_uploaded_image(db, upload))
    assert exc_info.value.status_code == 415
    assert exc_info.value.detail == "Only JPEG, PNG, and WEBP images are supported."


def test_search_rejects_empty_file(db):
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(search_uploaded_image(db, make_upload(b"")))
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Image file is empty."


def test_search_rejects_invalid_image_bytes(db):
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(search_uploaded_image(db, make_upload(b"not an image at all")))
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Invalid image file."


def test_search_rejects_oversized_file(db, monkeypatch):
    monkeypatch.setattr(dependencies.settings, "max_image_bytes", 10)
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(search_uploaded_image(db, make_upload(png_bytes())))
    assert exc_info.value.status_code == 413
    assert exc_info.value.detail == "Image is larger than 0 MB."
