from datetime import datetime

from pydantic import BaseModel, Field


def image_content_url(image_id: str) -> str:
    return f"/api/images/{image_id}/content"


class BoundingBox(BaseModel):
    x: float = Field(..., ge=0.0, le=1.0)
    y: float = Field(..., ge=0.0, le=1.0)
    width: float = Field(..., ge=0.0, le=1.0)
    height: float = Field(..., ge=0.0, le=1.0)


class OcrBoxOut(BaseModel):
    id: str
    text: str = Field(..., min_length=1)
    confidence: float = Field(..., ge=0.0, le=1.0)
    bbox: BoundingBox
    polygon: list[list[float]]


class SavedImageResponse(BaseModel):
    image_id: str
    image_width: int = Field(..., gt=0)
    image_height: int = Field(..., gt=0)
    boxes: list[OcrBoxOut]
    image_url: str
    filename: str | None = None
    content_type: str | None = None


class ImageMatch(BaseModel):
    image_id: str
    image_url: str
    filename: str | None = None
    image_width: int = Field(..., gt=0)
    image_height: int = Field(..., gt=0)
    similarity: float


class ImageSearchResponse(BaseModel):
    upload_id: str
    image_width: int = Field(..., gt=0)
    image_height: int = Field(..., gt=0)
    matches: list[ImageMatch]


class GalleryImage(BaseModel):
    image_id: str
    image_url: str
    filename: str | None = None
    image_width: int = Field(..., gt=0)
    image_height: int = Field(..., gt=0)
    created_at: datetime


class ImageListResponse(BaseModel):
    images: list[GalleryImage]
    limit: int = Field(..., gt=0)
    offset: int = Field(..., ge=0)
    has_more: bool
