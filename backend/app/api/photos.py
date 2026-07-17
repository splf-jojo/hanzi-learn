from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.photos import PhotoOut
from ..services import photos as photos_service

router = APIRouter(prefix="/api", tags=["photos"])


@router.get("/photos/{photo_id}", response_model=PhotoOut)
def get_photo(photo_id: int, db: Session = Depends(get_db)) -> PhotoOut:
    return photos_service.get_photo(db, photo_id)
