from argparse import ArgumentParser
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.orm import Session

from .character_sync import sync_characters_from_words
from .database import SessionLocal
from .models import (
    Character,
    Group,
    GroupWord,
    Photo,
    Sentence,
    UserCharacterProgress,
    UserWordProgress,
    Word,
    WordCharacter,
    WordSentence,
)
from .parsers import DEFAULT_MARKDOWN_DIR, ParsedData, load_markdown_data

BUILTIN_PHOTOS = [
    {
        "id": 1,
        "slug": "car",
        "filename": "car.png",
        "content_type": "image/png",
        "alt": "Car",
        "source": "frontend/images/car.png",
    },
    {
        "id": 2,
        "slug": "mushroom",
        "filename": "mushroom.png",
        "content_type": "image/png",
        "alt": "Mushroom",
        "source": "frontend/images/mushroom.png",
    },
    {
        "id": 3,
        "slug": "generated-water",
        "filename": "generated-water.png",
        "content_type": "image/png",
        "alt": "Water illustration",
        "source": "OpenAI imagegen; user-provided Chinese vintage mini-program prompt",
    },
    {
        "id": 4,
        "slug": "generated-apple",
        "filename": "generated-apple.png",
        "content_type": "image/png",
        "alt": "Apple illustration",
        "source": "OpenAI imagegen; user-provided Chinese vintage mini-program prompt",
    },
    {
        "id": 5,
        "slug": "generated-tea",
        "filename": "generated-tea.png",
        "content_type": "image/png",
        "alt": "Tea illustration",
        "source": "OpenAI imagegen; user-provided Chinese vintage mini-program prompt",
    },
    {
        "id": 6,
        "slug": "generated-cup",
        "filename": "generated-cup.png",
        "content_type": "image/png",
        "alt": "Cup illustration",
        "source": "OpenAI imagegen; user-provided Chinese vintage mini-program prompt",
    },
    {
        "id": 7,
        "slug": "generated-money",
        "filename": "generated-money.png",
        "content_type": "image/png",
        "alt": "Money illustration",
        "source": "OpenAI imagegen; user-provided Chinese vintage mini-program prompt",
    },
    {
        "id": 8,
        "slug": "generated-airplane",
        "filename": "generated-airplane.png",
        "content_type": "image/png",
        "alt": "Airplane illustration",
        "source": "OpenAI imagegen; user-provided Chinese vintage mini-program prompt",
    },
    {
        "id": 9,
        "slug": "generated-taxi",
        "filename": "generated-taxi.png",
        "content_type": "image/png",
        "alt": "Taxi illustration",
        "source": "OpenAI imagegen; user-provided Chinese vintage mini-program prompt",
    },
    {
        "id": 10,
        "slug": "generated-television",
        "filename": "generated-television.png",
        "content_type": "image/png",
        "alt": "Television illustration",
        "source": "OpenAI imagegen; user-provided Chinese vintage mini-program prompt",
    },
    {
        "id": 11,
        "slug": "generated-computer",
        "filename": "generated-computer.png",
        "content_type": "image/png",
        "alt": "Computer illustration",
        "source": "OpenAI imagegen; user-provided Chinese vintage mini-program prompt",
    },
    {
        "id": 12,
        "slug": "generated-book",
        "filename": "generated-book.png",
        "content_type": "image/png",
        "alt": "Book illustration",
        "source": "OpenAI imagegen; user-provided Chinese vintage mini-program prompt",
    },
    {
        "id": 13,
        "slug": "fish",
        "filename": "fish.png",
        "content_type": "image/png",
        "alt": "Fish illustration",
        "source": "frontend/images/fish.png",
    },
]


def normalize_photo_slug(value: str) -> str:
    return Path(value.strip()).stem.lower()


def photo_id_for_slug(raw_slug: str, photo_by_slug: dict[str, Photo]) -> int | None:
    if not raw_slug:
        return None

    photo = photo_by_slug.get(normalize_photo_slug(raw_slug))
    return photo.id if photo else None


def sentence_matches_word(sentence_hanzi: str, word_hanzi: str) -> bool:
    if word_hanzi in sentence_hanzi:
        return True

    if "……" not in word_hanzi:
        return False

    cursor = 0
    for part in [value.strip() for value in word_hanzi.split("……") if value.strip()]:
        next_index = sentence_hanzi.find(part, cursor)
        if next_index == -1:
            return False
        cursor = next_index + len(part)

    return True


def replace_data(db: Session, data: ParsedData) -> None:
    db.query(UserCharacterProgress).delete()
    db.query(UserWordProgress).delete()
    db.query(WordSentence).delete()
    db.query(WordCharacter).delete()
    db.query(Character).delete()
    db.query(GroupWord).delete()
    db.query(Group).delete()
    db.query(Sentence).delete()
    db.query(Word).delete()
    db.query(Photo).delete()

    photos = [Photo(**photo_data) for photo_data in BUILTIN_PHOTOS]
    db.add_all(photos)
    db.flush()
    if db.bind is not None and db.bind.dialect.name == "postgresql":
        db.execute(text("SELECT setval('photos_id_seq', GREATEST((SELECT COALESCE(MAX(id), 1) FROM photos), 1), true)"))

    photo_by_slug = {photo.slug: photo for photo in photos}

    db.add_all(
        Word(
            id=word.id,
            hanzi=word.hanzi,
            pinyin=word.pinyin,
            translation=word.translation,
            description=word.description,
            image="",
            photo_id=photo_id_for_slug(word.photo_slug, photo_by_slug),
            position=word.position,
        )
        for word in data.words
    )
    db.add_all(
        Sentence(
            id=sentence.id,
            hanzi=sentence.hanzi,
            pinyin=sentence.pinyin,
            translation=sentence.translation,
            description=sentence.description,
            position=sentence.position,
        )
        for sentence in data.sentences
    )
    db.add_all(
        Group(id=group.id, name=group.name, description=group.description, position=group.position)
        for group in data.groups
    )
    db.flush()

    db.add_all(
        GroupWord(group_id=group.id, word_id=word_id, position=position)
        for group in data.groups
        for position, word_id in enumerate(group.words)
    )
    db.add_all(
        WordSentence(word_id=word.id, sentence_id=sentence.id)
        for word in data.words
        for sentence in data.sentences
        if sentence_matches_word(sentence.hanzi, word.hanzi)
    )
    sync_characters_from_words(db)


def seed_database(markdown_dir: Path = DEFAULT_MARKDOWN_DIR) -> ParsedData:
    data = load_markdown_data(markdown_dir)

    with SessionLocal() as db:
        replace_data(db, data)
        db.commit()

    return data


def main() -> None:
    parser = ArgumentParser(description="Import markdown learning data into the normalized Chinese vocab schema.")
    parser.add_argument("--markdown-dir", type=Path, default=DEFAULT_MARKDOWN_DIR)
    args = parser.parse_args()

    data = seed_database(args.markdown_dir)
    print(f"Imported {len(data.words)} words, {len(data.sentences)} sentences, {len(data.groups)} groups.")


if __name__ == "__main__":
    main()
