import unicodedata

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Character, Word, WordCharacter

PINYIN_INITIALS = [
    "zh",
    "ch",
    "sh",
    "b",
    "p",
    "m",
    "f",
    "d",
    "t",
    "n",
    "l",
    "g",
    "k",
    "h",
    "j",
    "q",
    "x",
    "r",
    "z",
    "c",
    "s",
    "y",
    "w",
]
PINYIN_FINALS = [
    "uang",
    "iang",
    "iong",
    "ueng",
    "ang",
    "eng",
    "ing",
    "ong",
    "iao",
    "ian",
    "uai",
    "uan",
    "van",
    "ai",
    "ei",
    "ao",
    "ou",
    "an",
    "en",
    "in",
    "un",
    "ia",
    "ie",
    "iu",
    "ua",
    "uo",
    "ui",
    "ue",
    "ve",
    "er",
    "ar",
    "a",
    "o",
    "e",
    "i",
    "u",
    "v",
    "m",
    "n",
    "r",
]
UMLAUTED_U = str.maketrans({"ü": "v", "ǖ": "v", "ǘ": "v", "ǚ": "v", "ǜ": "v"})


def is_han_character(value: str) -> bool:
    if len(value) != 1:
        return False

    name = unicodedata.name(value, "")
    return "CJK UNIFIED IDEOGRAPH" in name or "CJK COMPATIBILITY IDEOGRAPH" in name


def han_characters(value: str) -> list[str]:
    return [character for character in value if is_han_character(character)]


def normalize_pinyin_character(value: str) -> str:
    normalized_value = value.translate(UMLAUTED_U)
    return "".join(
        character
        for character in unicodedata.normalize("NFD", normalized_value).lower()
        if unicodedata.category(character) != "Mn"
    )


def compact_pinyin(pinyin: str) -> tuple[str, list[str]]:
    normalized_parts = []
    original_characters = []

    for character in pinyin:
        if character.isspace() or character in "'’.-":
            continue

        normalized_character = normalize_pinyin_character(character)
        if not normalized_character.isalpha():
            continue

        normalized_parts.append(normalized_character)
        original_characters.append(character)

    return "".join(normalized_parts), original_characters


def pinyin_syllable_length_at(source: str, cursor: int) -> int:
    initial = next((value for value in PINYIN_INITIALS if source.startswith(value, cursor)), "")
    final_cursor = cursor + len(initial)
    final = next((value for value in PINYIN_FINALS if source.startswith(value, final_cursor)), "")

    return len(initial) + len(final) if final else 1


def split_pinyin_syllables(pinyin: str, expected_count: int) -> list[str]:
    spaced_tokens = [token for token in pinyin.strip().split() if token]
    if len(spaced_tokens) == expected_count:
        return spaced_tokens

    normalized, original_characters = compact_pinyin(pinyin)
    syllables = []
    cursor = 0

    while cursor < len(normalized) and len(syllables) < expected_count:
        syllable_length = pinyin_syllable_length_at(normalized, cursor)
        syllables.append("".join(original_characters[cursor : cursor + syllable_length]))
        cursor += syllable_length

    return syllables if len(syllables) == expected_count else spaced_tokens


def character_pinyin_for_word(word: Word, character_count: int, position: int) -> str:
    if not word.pinyin:
        return ""

    syllables = split_pinyin_syllables(word.pinyin, character_count)
    return syllables[position] if position < len(syllables) else ""


def describe_character_usage(occurrences: list[tuple[Word, int, str]]) -> str:
    examples = []
    seen_word_ids = set()

    for word, _, _ in occurrences:
        if word.id in seen_word_ids:
            continue

        seen_word_ids.add(word.id)
        details = f"{word.hanzi} ({word.pinyin})" if word.pinyin else word.hanzi
        if word.translation:
            details = f"{details} - {word.translation}"
        examples.append(details)

        if len(examples) == 6:
            break

    return "Appears in: " + "; ".join(examples) if examples else ""


def sync_characters_from_words(db: Session) -> int:
    words = list(db.scalars(select(Word).order_by(Word.position, Word.id)))
    single_character_words = {
        characters[0]: word
        for word in words
        if len(characters := han_characters(word.hanzi)) == 1 and word.hanzi == characters[0]
    }

    glyph_positions: dict[str, int] = {}
    glyph_occurrences: dict[str, list[tuple[Word, int, str]]] = {}
    for word in words:
        characters = han_characters(word.hanzi)
        for position, glyph in enumerate(characters):
            if glyph not in glyph_positions:
                glyph_positions[glyph] = len(glyph_positions)
            glyph_occurrences.setdefault(glyph, []).append(
                (word, position, character_pinyin_for_word(word, len(characters), position))
            )

    db.query(WordCharacter).delete()
    db.flush()

    existing_characters = {character.glyph: character for character in db.scalars(select(Character))}
    stale_glyphs = set(existing_characters) - set(glyph_positions)
    if stale_glyphs:
        db.query(Character).filter(Character.glyph.in_(stale_glyphs)).delete(synchronize_session=False)
        db.flush()

    characters_by_glyph: dict[str, Character] = {}
    for glyph, position in glyph_positions.items():
        source_word = single_character_words.get(glyph)
        occurrences = glyph_occurrences.get(glyph, [])
        first_pinyin = next((pinyin for _, _, pinyin in occurrences if pinyin), "")
        translation = source_word.translation if source_word else next((word.translation for word, _, _ in occurrences if word.translation), "")
        character = existing_characters.get(glyph)
        if character is None:
            character = Character(glyph=glyph, position=position)
            db.add(character)

        character.pinyin = source_word.pinyin if source_word else first_pinyin
        character.translation = translation
        character.description = describe_character_usage(occurrences)
        character.image = source_word.image if source_word else ""
        character.position = position
        characters_by_glyph[glyph] = character

    db.flush()

    db.add_all(
        WordCharacter(
            word_id=word.id,
            character_id=characters_by_glyph[glyph].id,
            position=position,
            pinyin=character_pinyin_for_word(word, len(han_characters(word.hanzi)), position),
            role="",
        )
        for word in words
        for position, glyph in enumerate(han_characters(word.hanzi))
    )

    return len(characters_by_glyph)
