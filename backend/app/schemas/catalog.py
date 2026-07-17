from pydantic import BaseModel


class WordCharacterOut(BaseModel):
    word_id: int
    character_id: int
    # Исторический контракт фронта: дублирует character_id.
    id: int
    glyph: str
    position: int
    pinyin: str
    role: str


class CharacterOut(BaseModel):
    id: int
    glyph: str
    pinyin: str
    translation: str
    description: str
    radical: str
    strokes: int | None
    hsk_level: str
    image: str
    position: int


class SentenceOut(BaseModel):
    id: int
    hanzi: str
    pinyin: str
    translation: str
    description: str
    words: list[int]


class GroupOut(BaseModel):
    id: int
    words: list[int]
    name: str
    description: str
