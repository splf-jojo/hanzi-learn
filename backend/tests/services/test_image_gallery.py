import asyncio
from datetime import datetime, timezone
from io import BytesIO
from uuid import uuid4

import pytest
from fastapi import HTTPException
from PIL import Image as PILImage

from app.models import Image, OcrBox
from app.services.image_gallery import get_image_content, get_saved_image, list_saved_images


def png_bytes(color=(255, 0, 0)) -> bytes:
    buffer = BytesIO()
    PILImage.new("RGB", (4, 4), color).save(buffer, format="PNG")
    return buffer.getvalue()


def unit_vector(index: int, dim: int = 512) -> list[float]:
    values = [0.0] * dim
    values[index] = 1.0
    return values


def add_image(db, *, filename="img.png", created_at=None, embedding=None, data=None):
    image = Image(
        filename=filename,
        content_type="image/png",
        image_bytes=data if data is not None else png_bytes(),
        image_width=4,
        image_height=4,
        embedding=embedding if embedding is not None else unit_vector(0),
    )
    if created_at is not None:
        image.created_at = created_at
    db.add(image)
    db.flush()
    return image


def test_list_images_pagination_has_more(db):
    old = add_image(db, filename="old.png", created_at=datetime(2026, 7, 1, tzinfo=timezone.utc))
    middle = add_image(db, filename="middle.png", created_at=datetime(2026, 7, 2, tzinfo=timezone.utc))
    new = add_image(db, filename="new.png", created_at=datetime(2026, 7, 3, tzinfo=timezone.utc))

    first_page = asyncio.run(list_saved_images(db, 2, 0))
    assert first_page.limit == 2
    assert first_page.offset == 0
    assert first_page.has_more is True
    assert [image.image_id for image in first_page.images] == [str(new.id), str(middle.id)]
    assert first_page.images[0].image_url == f"/api/images/{new.id}/content"
    assert first_page.images[0].filename == "new.png"

    second_page = asyncio.run(list_saved_images(db, 2, 2))
    assert second_page.has_more is False
    assert [image.image_id for image in second_page.images] == [str(old.id)]


def test_get_image_returns_ordered_boxes(db):
    image = add_image(db, filename="boxed.png")
    # Вставка нарочно не по порядку box_order.
    for order, text in [(2, "third"), (0, "first"), (1, "second")]:
        db.add(
            OcrBox(
                image_id=image.id,
                box_order=order,
                text=text,
                confidence=0.9,
                bbox={"x": 0.1, "y": 0.2, "width": 0.3, "height": 0.1},
                polygon=[[0.1, 0.2], [0.4, 0.2], [0.4, 0.3], [0.1, 0.3]],
            )
        )
    db.flush()

    saved = asyncio.run(get_saved_image(db, str(image.id)))
    assert saved.image_id == str(image.id)
    assert saved.image_url == f"/api/images/{image.id}/content"
    assert saved.filename == "boxed.png"
    assert saved.content_type == "image/png"
    assert saved.image_width == 4
    assert saved.image_height == 4
    assert [box.text for box in saved.boxes] == ["first", "second", "third"]
    assert saved.boxes[0].bbox.x == pytest.approx(0.1)
    assert saved.boxes[0].polygon == [[0.1, 0.2], [0.4, 0.2], [0.4, 0.3], [0.1, 0.3]]


def test_get_image_invalid_uuid_returns_404(db):
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(get_saved_image(db, "not-a-uuid"))
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Saved image was not found."


def test_get_image_unknown_id_returns_404(db):
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(get_saved_image(db, str(uuid4())))
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Saved image was not found."


def test_get_content_returns_bytes_and_content_type(db):
    data = png_bytes(color=(0, 128, 255))
    image = add_image(db, filename="content.png", data=data)

    content = asyncio.run(get_image_content(db, str(image.id)))
    assert content.image_bytes == data
    assert content.content_type == "image/png"
    assert content.filename == "content.png"


def test_get_content_invalid_uuid_returns_404(db):
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(get_image_content(db, "42"))
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Saved image was not found."
