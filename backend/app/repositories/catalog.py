from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..models import Character, Group, Sentence, WordCharacter


def list_sentences(db: Session) -> list[Sentence]:
    return list(
        db.scalars(
            select(Sentence)
            .options(selectinload(Sentence.word_links))
            .order_by(Sentence.position, Sentence.id)
        )
    )


def list_characters(db: Session) -> list[Character]:
    return list(db.scalars(select(Character).order_by(Character.position, Character.id)))


def list_word_characters(db: Session) -> list[WordCharacter]:
    return list(
        db.scalars(
            select(WordCharacter)
            .options(selectinload(WordCharacter.character))
            .order_by(WordCharacter.word_id, WordCharacter.position)
        )
    )


def list_groups(db: Session) -> list[Group]:
    return list(
        db.scalars(
            select(Group)
            .options(selectinload(Group.word_links))
            .order_by(Group.position, Group.id)
        )
    )
