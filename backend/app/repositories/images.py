from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, defer, selectinload

from ..models import Image, OcrBox


def save_image(
    db: Session,
    *,
    filename: str,
    content_type: str,
    image_bytes: bytes,
    image_width: int,
    image_height: int,
    embedding: list[float],
    boxes: list[dict],
) -> Image:
    image = Image(
        filename=filename,
        content_type=content_type,
        image_bytes=image_bytes,
        image_width=image_width,
        image_height=image_height,
        embedding=embedding,
    )
    for index, box in enumerate(boxes):
        image.boxes.append(
            OcrBox(
                box_order=index,
                text=box["text"],
                confidence=box["confidence"],
                bbox=box["bbox"],
                polygon=box["polygon"],
            )
        )
    db.add(image)
    db.flush()
    return image


def list_images(db: Session, limit: int, offset: int) -> tuple[list[Image], bool]:
    rows = (
        db.execute(
            select(Image)
            .options(defer(Image.embedding))
            .order_by(Image.created_at.desc(), Image.id.desc())
            .limit(limit + 1)
            .offset(offset)
        )
        .scalars()
        .all()
    )
    has_more = len(rows) > limit
    return list(rows[:limit]), has_more


def get_image(db: Session, image_id: uuid.UUID) -> Image | None:
    return db.execute(
        select(Image)
        .options(defer(Image.embedding), selectinload(Image.boxes))
        .where(Image.id == image_id)
    ).scalar_one_or_none()


def get_content(db: Session, image_id: uuid.UUID) -> tuple[bytes, str, str] | None:
    row = db.execute(
        select(Image.image_bytes, Image.content_type, Image.filename).where(Image.id == image_id)
    ).first()
    if row is None:
        return None
    return bytes(row.image_bytes), row.content_type, row.filename


def search_similar(db: Session, embedding: list[float], top_k: int = 5) -> list[tuple[Image, float]]:
    distance = Image.embedding.cosine_distance(embedding)
    rows = db.execute(
        select(Image, distance.label("distance"))
        .options(defer(Image.embedding))
        .order_by(distance)
        .limit(top_k)
    ).all()
    return [(image, 1.0 - float(dist)) for image, dist in rows]
