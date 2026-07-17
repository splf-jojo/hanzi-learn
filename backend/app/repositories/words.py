from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..models.learning import Photo, Word, WordCharacter


def list_words(db: Session) -> list[Word]:
    return list(
        db.scalars(
            select(Word)
            .options(selectinload(Word.character_links).selectinload(WordCharacter.character))
            .order_by(Word.position, Word.id)
        )
    )


def get_word(db: Session, word_id: int) -> Word | None:
    return db.get(Word, word_id)


def get_photo(db: Session, photo_id: int) -> Photo | None:
    return db.get(Photo, photo_id)


def get_photo_by_slug(db: Session, slug: str) -> Photo | None:
    return db.scalar(select(Photo).where(Photo.slug == slug))


def set_word_photo(db: Session, word: Word, photo_id: int | None) -> None:
    word.photo_id = photo_id
