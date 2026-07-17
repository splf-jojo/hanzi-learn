import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.constants import DEFAULT_USER_ID
from app.models.learning import Word
from app.models.progress import UserWordProgress
from app.repositories import progress as progress_repository
from app.schemas.progress import KnowledgeLevelUpdate
from app.services import words as words_service


def make_word(db, hanzi="你好", position=1):
    word = Word(hanzi=hanzi, position=position)
    db.add(word)
    db.flush()
    return word


def test_update_knowledge_level_creates_progress(db):
    word = make_word(db)

    result = words_service.update_knowledge_level(db, word.id, KnowledgeLevelUpdate(knowledge_level=3))

    assert result.id == word.id
    assert result.knowledge_level == 3
    row = db.get(UserWordProgress, (DEFAULT_USER_ID, word.id))
    assert row is not None
    assert row.knowledge_level == 3


def test_update_knowledge_level_updates_existing_row(db):
    word = make_word(db)
    db.add(UserWordProgress(user_id=DEFAULT_USER_ID, word_id=word.id, knowledge_level=1))
    db.flush()

    result = words_service.update_knowledge_level(db, word.id, KnowledgeLevelUpdate(knowledge_level=5))

    assert result.knowledge_level == 5
    assert progress_repository.progress_map(db, DEFAULT_USER_ID) == {word.id: 5}


def test_update_knowledge_level_to_zero(db):
    word = make_word(db)
    db.add(UserWordProgress(user_id=DEFAULT_USER_ID, word_id=word.id, knowledge_level=4))
    db.flush()

    result = words_service.update_knowledge_level(db, word.id, KnowledgeLevelUpdate(knowledge_level=0))

    assert result.knowledge_level == 0
    assert progress_repository.progress_map(db, DEFAULT_USER_ID) == {word.id: 0}


def test_update_knowledge_level_word_not_found(db):
    with pytest.raises(HTTPException) as exc_info:
        words_service.update_knowledge_level(db, 999_999, KnowledgeLevelUpdate(knowledge_level=1))
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Word not found"


def test_progress_map_empty_and_default_zero(db):
    word = make_word(db)

    assert progress_repository.progress_map(db, DEFAULT_USER_ID) == {}
    assert words_service.list_words(db)[0].knowledge_level == 0
    assert words_service.word_to_schema(word, {}).knowledge_level == 0


@pytest.mark.parametrize("level", [0, 1, 5])
def test_schema_accepts_valid_levels(level):
    assert KnowledgeLevelUpdate(knowledge_level=level).knowledge_level == level


def test_schema_accepts_camel_case_alias():
    assert KnowledgeLevelUpdate.model_validate({"knowledgeLevel": 2}).knowledge_level == 2


@pytest.mark.parametrize(
    "payload",
    [
        {"knowledge_level": 6},
        {"knowledge_level": -1},
        {"knowledge_level": True},
        {"knowledge_level": False},
        {},
    ],
)
def test_schema_rejects_invalid_payloads(payload):
    with pytest.raises(ValidationError):
        KnowledgeLevelUpdate.model_validate(payload)
