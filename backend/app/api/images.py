from __future__ import annotations

from fastapi import APIRouter, Depends, File, Query, Response, UploadFile
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.images import ImageListResponse, ImageSearchResponse, SavedImageResponse
from ..services.image_gallery import get_image_content, get_saved_image, list_saved_images
from ..services.image_search import search_uploaded_image


router = APIRouter(prefix="/api/images", tags=["images"])


@router.post("/search", response_model=ImageSearchResponse)
async def search_similar_images(
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ImageSearchResponse:
    return await search_uploaded_image(db, image)


@router.get("", response_model=ImageListResponse)
async def list_images(
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> ImageListResponse:
    return await list_saved_images(db, limit, offset)


@router.get("/{image_id}", response_model=SavedImageResponse)
async def get_image(image_id: str, db: Session = Depends(get_db)) -> SavedImageResponse:
    return await get_saved_image(db, image_id)


@router.get("/{image_id}/content")
async def get_image_content_response(image_id: str, db: Session = Depends(get_db)) -> Response:
    content = await get_image_content(db, image_id)
    return Response(content=content.image_bytes, media_type=content.content_type)
