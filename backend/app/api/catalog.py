from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.catalog import CharacterOut, GroupOut, SentenceOut, WordCharacterOut
from ..services import catalog as catalog_service

router = APIRouter(prefix="/api", tags=["catalog"])


@router.get("/sentences", response_model=list[SentenceOut])
def sentences(db: Session = Depends(get_db)) -> list[SentenceOut]:
    return catalog_service.list_sentences(db)


@router.get("/characters", response_model=list[CharacterOut])
def characters(db: Session = Depends(get_db)) -> list[CharacterOut]:
    return catalog_service.list_characters(db)


@router.get("/word-characters", response_model=list[WordCharacterOut])
def word_characters(db: Session = Depends(get_db)) -> list[WordCharacterOut]:
    return catalog_service.list_word_characters(db)


@router.get("/groups", response_model=list[GroupOut])
def groups(db: Session = Depends(get_db)) -> list[GroupOut]:
    return catalog_service.list_groups(db)
