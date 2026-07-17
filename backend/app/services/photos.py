from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..models.learning import Photo
from ..repositories import words as words_repository
from ..schemas.photos import PhotoOut


def photo_to_schema(photo: Photo) -> PhotoOut:
    return PhotoOut(
        id=photo.id,
        slug=photo.slug,
        filename=photo.filename,
        content_type=photo.content_type,
        alt=photo.alt,
        source=photo.source,
        url=f"/api/photo-files/{photo.filename}",
    )


def get_photo(db: Session, photo_id: int) -> PhotoOut:
    photo = words_repository.get_photo(db, photo_id)
    if photo is None:
        raise HTTPException(status_code=404, detail="Photo not found")

    return photo_to_schema(photo)
