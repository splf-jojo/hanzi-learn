import pytest
from fastapi import HTTPException

from app.constants import DEFAULT_USER_ID
from app.models.learning import Character, Photo, Word, WordCharacter
from app.models.progress import UserWordProgress
from app.schemas.words import WordPhotoUpdate
from app.services import photos as photos_service
from app.services import words as words_service


def make_word(db, hanzi="你好", position=1, **kwargs):
    word = Word(hanzi=hanzi, position=position, **kwargs)
    db.add(word)
    db.flush()
    return word


def make_photo(db, slug="cat", filename="cat.png"):
    photo = Photo(slug=slug, filename=filename)
    db.add(photo)
    db.flush()
    return photo


def test_list_words_empty(db):
    assert words_service.list_words(db) == []


def test_list_words_orders_and_applies_progress(db):
    ni = Character(glyph="你", position=1)
    hao = Character(glyph="好", position=2)
    db.add_all([ni, hao])
    db.flush()

    second = make_word(db, hanzi="好", position=2)
    first = make_word(db, hanzi="你好", position=1)
    db.add_all(
        [
            WordCharacter(word_id=first.id, character_id=ni.id, position=0, pinyin="nǐ"),
            WordCharacter(word_id=first.id, character_id=hao.id, position=1, pinyin="hǎo"),
        ]
    )
    db.add(UserWordProgress(user_id=DEFAULT_USER_ID, word_id=first.id, knowledge_level=4))
    db.flush()

    result = words_service.list_words(db)

    assert [word.id for word in result] == [first.id, second.id]
    assert result[0].knowledge_level == 4
    assert result[1].knowledge_level == 0

    characters = result[0].characters
    assert [c.glyph for c in characters] == ["你", "好"]
    assert characters[0].word_id == first.id
    assert characters[0].character_id == ni.id
    # исторический контракт: id дублирует character_id
    assert characters[0].id == ni.id
    assert characters[0].pinyin == "nǐ"


def test_list_words_ignores_other_users_progress(db):
    word = make_word(db)
    db.add(UserWordProgress(user_id="someone-else", word_id=word.id, knowledge_level=5))
    db.flush()

    assert words_service.list_words(db)[0].knowledge_level == 0


def test_get_photo_returns_schema(db):
    photo = make_photo(db, slug="tea", filename="tea.jpg")

    result = photos_service.get_photo(db, photo.id)

    assert result.id == photo.id
    assert result.slug == "tea"
    assert result.url == "/api/photo-files/tea.jpg"


def test_get_photo_not_found(db):
    with pytest.raises(HTTPException) as exc_info:
        photos_service.get_photo(db, 999_999)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Photo not found"


def test_get_word_photo(db):
    photo = make_photo(db)
    word = make_word(db, photo_id=photo.id)

    result = words_service.get_word_photo(db, word.id)

    assert result.id == photo.id
    assert result.url == "/api/photo-files/cat.png"


def test_get_word_photo_word_not_found(db):
    with pytest.raises(HTTPException) as exc_info:
        words_service.get_word_photo(db, 999_999)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Word not found"


def test_get_word_photo_without_photo(db):
    word = make_word(db)

    with pytest.raises(HTTPException) as exc_info:
        words_service.get_word_photo(db, word.id)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Word photo not found"


def test_update_word_photo_attach_by_id(db):
    word = make_word(db)
    photo = make_photo(db)

    result = words_service.update_word_photo(db, word.id, WordPhotoUpdate(photo_id=photo.id))

    assert result.word_id == word.id
    assert result.photo is not None
    assert result.photo.id == photo.id
    assert result.photo.url == "/api/photo-files/cat.png"
    assert word.photo_id == photo.id


def test_update_word_photo_attach_by_slug_alias(db):
    word = make_word(db)
    photo = make_photo(db, slug="dog", filename="dog.png")

    payload = WordPhotoUpdate.model_validate({"slug": "dog"})
    result = words_service.update_word_photo(db, word.id, payload)

    assert result.photo is not None
    assert result.photo.id == photo.id
    assert word.photo_id == photo.id


def test_update_word_photo_detach(db):
    photo = make_photo(db)
    word = make_word(db, photo_id=photo.id)

    result = words_service.update_word_photo(db, word.id, WordPhotoUpdate())

    assert result.word_id == word.id
    assert result.photo is None
    assert word.photo_id is None


def test_update_word_photo_word_not_found(db):
    with pytest.raises(HTTPException) as exc_info:
        words_service.update_word_photo(db, 999_999, WordPhotoUpdate())
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Word not found"


def test_update_word_photo_unknown_photo_id(db):
    word = make_word(db)

    with pytest.raises(HTTPException) as exc_info:
        words_service.update_word_photo(db, word.id, WordPhotoUpdate(photo_id=999_999))
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Photo not found"
    assert word.photo_id is None


def test_update_word_photo_unknown_slug(db):
    word = make_word(db)

    with pytest.raises(HTTPException) as exc_info:
        words_service.update_word_photo(db, word.id, WordPhotoUpdate(photo_slug="missing"))
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Photo not found"
