from sqlalchemy import select

from app.models import Character, Word, WordCharacter
from app.services.character_sync import sync_characters_from_words


def add_words(db, *words: Word) -> None:
    db.add_all(words)
    db.flush()


def test_sync_creates_characters_with_positional_pinyin(db):
    add_words(
        db,
        Word(id=1, hanzi="你好", pinyin="nǐ hǎo", translation="hello", position=0),
        Word(id=2, hanzi="你", pinyin="nǐ", translation="you", position=1),
    )

    count = sync_characters_from_words(db)
    db.flush()

    assert count == 2
    characters = {character.glyph: character for character in db.scalars(select(Character))}
    assert set(characters) == {"你", "好"}
    # 你 берёт пиньинь/перевод из одиночного слова, 好 — из первого вхождения
    assert characters["你"].pinyin == "nǐ"
    assert characters["你"].translation == "you"
    assert characters["好"].pinyin == "hǎo"
    assert characters["好"].translation == "hello"
    assert characters["你"].description.startswith("Appears in:")

    links = db.scalars(
        select(WordCharacter).where(WordCharacter.word_id == 1).order_by(WordCharacter.position)
    ).all()
    assert [(link.position, link.pinyin) for link in links] == [(0, "nǐ"), (1, "hǎo")]
    assert links[0].character_id == characters["你"].id
    assert links[1].character_id == characters["好"].id


def test_sync_rebuilds_links_and_prunes_stale_characters(db):
    add_words(
        db,
        Word(id=1, hanzi="你好", pinyin="nǐ hǎo", translation="hello", position=0),
        Word(id=2, hanzi="你", pinyin="nǐ", translation="you", position=1),
    )
    sync_characters_from_words(db)
    db.flush()

    db.delete(db.get(Word, 1))
    db.flush()

    count = sync_characters_from_words(db)
    db.flush()

    assert count == 1
    assert set(db.scalars(select(Character.glyph))) == {"你"}
    links = db.scalars(select(WordCharacter)).all()
    assert [(link.word_id, link.position, link.pinyin) for link in links] == [(2, 0, "nǐ")]
