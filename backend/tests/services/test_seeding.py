from sqlalchemy import func, select

from app.models import Character, Group, GroupWord, Photo, Sentence, Word, WordSentence
from app.services.seeding import BUILTIN_PHOTOS, seed_database

WORDS_MD = """\
| id | Word | Pinyin | Translation | Photo |
| --- | --- | --- | --- | --- |
| 1 | 你好 | nǐ hǎo | hello | car |
| 2 | 水 | shuǐ | water | |
"""

SENTENCES_MD = """\
| id | sentence | pinyin | translation |
| --- | --- | --- | --- |
| 1 | 你好！ | nǐ hǎo | Hello! |
"""

GROUPS_MD = """\
| id | words | название |
| --- | --- | --- |
| 1 | [1, 2] | Basics |
"""


def write_markdown_fixtures(directory):
    (directory / "words.md").write_text(WORDS_MD, encoding="utf-8")
    (directory / "sentence.md").write_text(SENTENCES_MD, encoding="utf-8")
    (directory / "groups.md").write_text(GROUPS_MD, encoding="utf-8")


def count_rows(db, model) -> int:
    return db.scalar(select(func.count()).select_from(model))


def test_seed_database_loads_markdown(db, tmp_path):
    write_markdown_fixtures(tmp_path)

    data = seed_database(markdown_dir=tmp_path, db=db)

    assert data is not None
    assert count_rows(db, Word) == 2
    assert count_rows(db, Sentence) == 1
    assert count_rows(db, Group) == 1
    assert count_rows(db, Photo) == len(BUILTIN_PHOTOS)

    word = db.get(Word, 1)
    assert word.hanzi == "你好"
    assert word.photo_id == 1  # slug "car" из BUILTIN_PHOTOS

    links = db.scalars(select(WordSentence)).all()
    assert [(link.word_id, link.sentence_id) for link in links] == [(1, 1)]

    group_links = db.scalars(select(GroupWord).order_by(GroupWord.position)).all()
    assert [(link.group_id, link.word_id) for link in group_links] == [(1, 1), (1, 2)]

    assert set(db.scalars(select(Character.glyph))) == {"你", "好", "水"}


def test_seed_database_only_if_empty_skips_existing_data(db, tmp_path):
    write_markdown_fixtures(tmp_path)
    seed_database(markdown_dir=tmp_path, db=db)

    word = db.get(Word, 1)
    word.translation = "marker"
    db.flush()

    result = seed_database(markdown_dir=tmp_path, only_if_empty=True, db=db)

    assert result is None
    assert count_rows(db, Word) == 2
    assert db.get(Word, 1).translation == "marker"
