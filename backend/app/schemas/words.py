from pydantic import AliasChoices, BaseModel, Field

from .catalog import WordCharacterOut
from .photos import PhotoOut


class WordOut(BaseModel):
    id: int
    hanzi: str
    pinyin: str
    translation: str
    description: str
    part_of_speech: str
    level: str
    photo_id: int | None
    position: int
    knowledge_level: int
    characters: list[WordCharacterOut]


class WordPhotoUpdate(BaseModel):
    photo_id: int | None = Field(
        default=None, validation_alias=AliasChoices("photo_id", "photoId")
    )
    photo_slug: str | None = Field(
        default=None, validation_alias=AliasChoices("photo_slug", "photoSlug", "slug")
    )


class WordPhotoUpdateResult(BaseModel):
    word_id: int
    photo: PhotoOut | None
