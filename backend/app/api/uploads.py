from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.images import SavedImageResponse
from ..services.upload_save import save_upload


router = APIRouter(prefix="/api/uploads", tags=["uploads"])


@router.post("/{upload_id}/save", response_model=SavedImageResponse)
async def save_pending_upload(upload_id: str, db: Session = Depends(get_db)) -> SavedImageResponse:
    return await save_upload(db, upload_id)
