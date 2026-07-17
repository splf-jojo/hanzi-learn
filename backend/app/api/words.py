from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.photos import PhotoOut
from ..schemas.progress import KnowledgeLevelUpdate
from ..schemas.words import WordOut, WordPhotoUpdate, WordPhotoUpdateResult
from ..services import words as words_service

router = APIRouter(prefix="/api", tags=["words"])


@router.get("/words", response_model=list[WordOut])
def list_words(db: Session = Depends(get_db)) -> list[WordOut]:
    return words_service.list_words(db)


@router.get("/words/{word_id}/photo", response_model=PhotoOut)
def get_word_photo(word_id: int, db: Session = Depends(get_db)) -> PhotoOut:
    return words_service.get_word_photo(db, word_id)


@router.patch("/words/{word_id}/photo", response_model=WordPhotoUpdateResult)
def update_word_photo(
    word_id: int, payload: WordPhotoUpdate, db: Session = Depends(get_db)
) -> WordPhotoUpdateResult:
    return words_service.update_word_photo(db, word_id, payload)


@router.patch("/word-progress/{word_id}/knowledge-level", response_model=WordOut)
def update_knowledge_level(
    word_id: int, payload: KnowledgeLevelUpdate, db: Session = Depends(get_db)
) -> WordOut:
    return words_service.update_knowledge_level(db, word_id, payload)
