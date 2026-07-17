from app.models import (
    Character,
    Group,
    GroupWord,
    Sentence,
    Word,
    WordCharacter,
    WordSentence,
)
from app.services import catalog, learning_data


def make_word(db, hanzi: str, position: int) -> Word:
    word = Word(hanzi=hanzi, position=position)
    db.add(word)
    db.flush()
    return word


def make_character(db, glyph: str, position: int) -> Character:
    character = Character(glyph=glyph, position=position)
    db.add(character)
    db.flush()
    return character


def test_list_sentences_includes_word_ids(db):
    first_word = make_word(db, "你", 0)
    second_word = make_word(db, "好", 1)
    sentence = Sentence(hanzi="你好", position=0)
    db.add(sentence)
    db.flush()
    db.add(WordSentence(word_id=first_word.id, sentence_id=sentence.id))
    db.add(WordSentence(word_id=second_word.id, sentence_id=sentence.id))
    db.flush()

    result = catalog.list_sentences(db)

    assert [item.id for item in result] == [sentence.id]
    assert result[0].hanzi == "你好"
    assert sorted(result[0].words) == sorted([first_word.id, second_word.id])


def test_list_groups_orders_words_by_position(db):
    words = [make_word(db, glyph, index) for index, glyph in enumerate(["一", "二", "三"])]
    group = Group(name="numbers", position=0)
    db.add(group)
    db.flush()
    db.add(GroupWord(group_id=group.id, word_id=words[2].id, position=0))
    db.add(GroupWord(group_id=group.id, word_id=words[0].id, position=1))
    db.add(GroupWord(group_id=group.id, word_id=words[1].id, position=2))
    db.flush()
    db.expire_all()

    result = catalog.list_groups(db)

    assert [item.id for item in result] == [group.id]
    assert result[0].words == [words[2].id, words[0].id, words[1].id]


def test_list_characters_orders_by_position_then_id(db):
    late = make_character(db, "水", 5)
    early = make_character(db, "火", 1)
    middle = make_character(db, "土", 3)

    result = catalog.list_characters(db)

    assert [item.id for item in result] == [early.id, middle.id, late.id]
    assert [item.glyph for item in result] == ["火", "土", "水"]


def test_get_learning_data_composes_all_domains(db):
    word = make_word(db, "马", 0)
    character = make_character(db, "马", 0)
    db.add(WordCharacter(word_id=word.id, character_id=character.id, position=0))
    sentence = Sentence(hanzi="马来了", position=0)
    group = Group(name="animals", position=0)
    db.add_all([sentence, group])
    db.flush()
    db.add(WordSentence(word_id=word.id, sentence_id=sentence.id))
    db.add(GroupWord(group_id=group.id, word_id=word.id, position=0))
    db.flush()
    db.expire_all()

    result = learning_data.get_learning_data(db)

    payload = result.model_dump()
    assert set(payload) == {"words", "sentences", "groups", "characters", "word_characters"}
    assert [item.id for item in result.words] == [word.id]
    assert result.words[0].characters[0].character_id == character.id
    assert result.sentences[0].words == [word.id]
    assert result.groups[0].words == [word.id]
    assert [item.id for item in result.characters] == [character.id]
    assert result.word_characters[0].word_id == word.id
    assert result.word_characters[0].id == character.id
