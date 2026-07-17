from sqlalchemy.orm import Session

from ..models import Character, Group, Sentence
from ..repositories import catalog as catalog_repo
from ..schemas.catalog import CharacterOut, GroupOut, SentenceOut, WordCharacterOut
from .words import word_character_to_schema


def sentence_to_schema(sentence: Sentence) -> SentenceOut:
    return SentenceOut(
        id=sentence.id,
        hanzi=sentence.hanzi,
        pinyin=sentence.pinyin,
        translation=sentence.translation,
        description=sentence.description,
        words=[link.word_id for link in sentence.word_links],
    )


def character_to_schema(character: Character) -> CharacterOut:
    return CharacterOut(
        id=character.id,
        glyph=character.glyph,
        pinyin=character.pinyin,
        translation=character.translation,
        description=character.description,
        radical=character.radical,
        strokes=character.strokes,
        hsk_level=character.hsk_level,
        image=character.image,
        position=character.position,
    )


def group_to_schema(group: Group) -> GroupOut:
    return GroupOut(
        id=group.id,
        words=[link.word_id for link in group.word_links],
        name=group.name,
        description=group.description,
    )


def list_sentences(db: Session) -> list[SentenceOut]:
    return [sentence_to_schema(sentence) for sentence in catalog_repo.list_sentences(db)]


def list_characters(db: Session) -> list[CharacterOut]:
    return [character_to_schema(character) for character in catalog_repo.list_characters(db)]


def list_word_characters(db: Session) -> list[WordCharacterOut]:
    return [word_character_to_schema(link) for link in catalog_repo.list_word_characters(db)]


def list_groups(db: Session) -> list[GroupOut]:
    return [group_to_schema(group) for group in catalog_repo.list_groups(db)]
