from dataclasses import dataclass
from pathlib import Path
import re


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_MARKDOWN_DIR = ROOT_DIR / "backend" / "data"
DIVIDER_RE = re.compile(r"^:?-{3,}:?$")


@dataclass(frozen=True)
class ParsedWord:
    id: int
    hanzi: str
    pinyin: str
    translation: str
    description: str
    photo_slug: str
    position: int


@dataclass(frozen=True)
class ParsedSentence:
    id: int
    hanzi: str
    pinyin: str
    translation: str
    description: str
    position: int


@dataclass(frozen=True)
class ParsedGroup:
    id: int
    words: list[int]
    name: str
    description: str
    position: int


@dataclass(frozen=True)
class ParsedData:
    words: list[ParsedWord]
    sentences: list[ParsedSentence]
    groups: list[ParsedGroup]


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().strip("\"'`"))


def cells_from_table_row(raw_line: str) -> list[str] | None:
    if "|" not in raw_line:
        return None

    cells = [clean(cell) for cell in raw_line.split("|")]
    cells = [cell for cell in cells if cell]

    if not cells or all(DIVIDER_RE.match(cell) for cell in cells):
        return None

    return cells


def int_or_none(value: str) -> int | None:
    try:
        return int(value)
    except ValueError:
        return None


def read_markdown(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def read_first_existing_markdown(*paths: Path) -> str:
    for path in paths:
        if path.exists():
            return read_markdown(path)

    raise FileNotFoundError(paths[0])


def parse_words(markdown: str) -> list[ParsedWord]:
    words: list[ParsedWord] = []

    for line in markdown.splitlines():
        cells = cells_from_table_row(line)
        if not cells:
            continue

        word_id = int_or_none(cells[0])
        if word_id is None or len(cells) < 2:
            continue

        words.append(
            ParsedWord(
                id=word_id,
                hanzi=cells[1],
                pinyin=cells[2] if len(cells) > 2 else "",
                translation=cells[3] if len(cells) > 3 else "",
                description=cells[5] if len(cells) > 5 else "",
                photo_slug=cells[4] if len(cells) > 4 else "",
                position=len(words),
            )
        )

    return words


def parse_sentences(markdown: str) -> list[ParsedSentence]:
    sentences: list[ParsedSentence] = []

    for line in markdown.splitlines():
        cells = cells_from_table_row(line)
        if not cells:
            continue

        sentence_id = int_or_none(cells[0])
        if sentence_id is None or len(cells) < 2:
            continue

        sentences.append(
            ParsedSentence(
                id=sentence_id,
                hanzi=cells[1],
                pinyin=cells[2] if len(cells) > 2 else "",
                translation=cells[3] if len(cells) > 3 else "",
                description=cells[4] if len(cells) > 4 else "",
                position=len(sentences),
            )
        )

    return sentences


def parse_word_ids(value: str) -> list[int]:
    raw_ids = re.split(r"[,\s]+", value.strip().strip("[]"))
    return [word_id for raw_id in raw_ids if (word_id := int_or_none(raw_id)) is not None]


def parse_groups(markdown: str) -> list[ParsedGroup]:
    groups: list[ParsedGroup] = []

    for line in markdown.splitlines():
        cells = cells_from_table_row(line)
        if not cells:
            continue

        group_id = int_or_none(cells[0])
        if group_id is None or len(cells) < 3:
            continue

        groups.append(
            ParsedGroup(
                id=group_id,
                words=parse_word_ids(cells[1]),
                name=cells[2],
                description=cells[3] if len(cells) > 3 else "",
                position=len(groups),
            )
        )

    return groups


def load_markdown_data(markdown_dir: Path = DEFAULT_MARKDOWN_DIR) -> ParsedData:
    return ParsedData(
        words=parse_words(read_markdown(markdown_dir / "words.md")),
        sentences=parse_sentences(read_markdown(markdown_dir / "sentence.md")),
        groups=parse_groups(read_first_existing_markdown(markdown_dir / "groups.md", markdown_dir / "gropups.md")),
    )
