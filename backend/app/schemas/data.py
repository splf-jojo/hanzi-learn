from pydantic import BaseModel

from .catalog import CharacterOut, GroupOut, SentenceOut, WordCharacterOut
from .words import WordOut


class LearningDataOut(BaseModel):
    words: list[WordOut]
    sentences: list[SentenceOut]
    groups: list[GroupOut]
    characters: list[CharacterOut]
    word_characters: list[WordCharacterOut]
