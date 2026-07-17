from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..constants import DEFAULT_USER_ID
from ..models.learning import Word, WordCharacter
from ..repositories import progress as progress_repository
from ..repositories import words as words_repository
from ..schemas.catalog import WordCharacterOut
from ..schemas.photos import PhotoOut
from ..schemas.progress import KnowledgeLevelUpdate
from ..schemas.words import WordOut, WordPhotoUpdate, WordPhotoUpdateResult
from .photos import photo_to_schema


def word_character_to_schema(link: WordCharacter) -> WordCharacterOut:
    return WordCharacterOut(
        word_id=link.word_id,
        character_id=link.character_id,
        id=link.character_id,
        glyph=link.character.glyph,
        position=link.position,
        pinyin=link.pinyin,
        role=link.role,
    )


def word_to_schema(word: Word, progress: dict[int, int]) -> WordOut:
    return WordOut(
        id=word.id,
        hanzi=word.hanzi,
        pinyin=word.pinyin,
        translation=word.translation,
        description=word.description,
        part_of_speech=word.part_of_speech,
        level=word.level,
        photo_id=word.photo_id,
        position=word.position,
        knowledge_level=progress.get(word.id, 0),
        characters=[word_character_to_schema(link) for link in word.character_links],
    )


def list_words(db: Session) -> list[WordOut]:
    progress = progress_repository.progress_map(db, DEFAULT_USER_ID)
    return [word_to_schema(word, progress) for word in words_repository.list_words(db)]


def get_word_photo(db: Session, word_id: int) -> PhotoOut:
    word = words_repository.get_word(db, word_id)
    if word is None:
        raise HTTPException(status_code=404, detail="Word not found")

    if word.photo_id is None:
        raise HTTPException(status_code=404, detail="Word photo not found")

    photo = words_repository.get_photo(db, word.photo_id)
    if photo is None:
        raise HTTPException(status_code=404, detail="Photo not found")

    return photo_to_schema(photo)


def update_word_photo(db: Session, word_id: int, payload: WordPhotoUpdate) -> WordPhotoUpdateResult:
    word = words_repository.get_word(db, word_id)
    if word is None:
        raise HTTPException(status_code=404, detail="Word not found")

    if payload.photo_id is None and payload.photo_slug is None:
        words_repository.set_word_photo(db, word, None)
        db.commit()
        return WordPhotoUpdateResult(word_id=word.id, photo=None)

    if payload.photo_id is not None:
        photo = words_repository.get_photo(db, payload.photo_id)
    else:
        photo = words_repository.get_photo_by_slug(db, payload.photo_slug)

    if photo is None:
        raise HTTPException(status_code=404, detail="Photo not found")

    words_repository.set_word_photo(db, word, photo.id)
    db.commit()
    return WordPhotoUpdateResult(word_id=word.id, photo=photo_to_schema(photo))


def update_knowledge_level(db: Session, word_id: int, payload: KnowledgeLevelUpdate) -> WordOut:
    word = words_repository.get_word(db, word_id)
    if word is None:
        raise HTTPException(status_code=404, detail="Word not found")

    progress = progress_repository.get_or_create_progress(db, DEFAULT_USER_ID, word_id)
    progress.knowledge_level = payload.knowledge_level
    db.commit()
    db.refresh(word)
    return word_to_schema(word, {word_id: payload.knowledge_level})
