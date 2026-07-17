from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class Word(Base):
    __tablename__ = "words"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hanzi: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    pinyin: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    translation: Mapped[str] = mapped_column(Text, nullable=False, default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    part_of_speech: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    level: Mapped[str] = mapped_column(String(40), nullable=False, default="")
    image: Mapped[str] = mapped_column(Text, nullable=False, default="")
    photo_id: Mapped[int | None] = mapped_column(ForeignKey("photos.id", ondelete="SET NULL"), nullable=True, index=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    photo: Mapped["Photo | None"] = relationship(back_populates="words")
    group_links: Mapped[list["GroupWord"]] = relationship(back_populates="word", cascade="all, delete-orphan")
    character_links: Mapped[list["WordCharacter"]] = relationship(
        back_populates="word",
        cascade="all, delete-orphan",
        order_by="WordCharacter.position",
    )
    sentence_links: Mapped[list["WordSentence"]] = relationship(back_populates="word", cascade="all, delete-orphan")
    progress_entries: Mapped[list["UserWordProgress"]] = relationship(back_populates="word", cascade="all, delete-orphan")


class Photo(Base):
    __tablename__ = "photos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), nullable=False, unique=True, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(80), nullable=False, default="image/png")
    alt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    source: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    words: Mapped[list[Word]] = relationship(back_populates="photo")


class Character(Base):
    __tablename__ = "characters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    glyph: Mapped[str] = mapped_column(String(8), nullable=False, unique=True, index=True)
    pinyin: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    translation: Mapped[str] = mapped_column(Text, nullable=False, default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    radical: Mapped[str] = mapped_column(String(16), nullable=False, default="")
    strokes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    hsk_level: Mapped[str] = mapped_column(String(40), nullable=False, default="")
    image: Mapped[str] = mapped_column(Text, nullable=False, default="")
    position: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    word_links: Mapped[list["WordCharacter"]] = relationship(
        back_populates="character",
        cascade="all, delete-orphan",
        order_by="WordCharacter.word_id",
    )
    progress_entries: Mapped[list["UserCharacterProgress"]] = relationship(
        back_populates="character",
        cascade="all, delete-orphan",
    )


class WordCharacter(Base):
    __tablename__ = "word_characters"

    word_id: Mapped[int] = mapped_column(ForeignKey("words.id", ondelete="CASCADE"), primary_key=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"), nullable=False, index=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False, primary_key=True)
    pinyin: Mapped[str] = mapped_column(String(160), nullable=False, default="")
    role: Mapped[str] = mapped_column(String(80), nullable=False, default="")

    word: Mapped[Word] = relationship(back_populates="character_links")
    character: Mapped[Character] = relationship(back_populates="word_links")


class Sentence(Base):
    __tablename__ = "sentences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hanzi: Mapped[str] = mapped_column(Text, nullable=False)
    pinyin: Mapped[str] = mapped_column(Text, nullable=False, default="")
    translation: Mapped[str] = mapped_column(Text, nullable=False, default="")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    position: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    word_links: Mapped[list["WordSentence"]] = relationship(back_populates="sentence", cascade="all, delete-orphan")


class WordSentence(Base):
    __tablename__ = "word_sentences"

    word_id: Mapped[int] = mapped_column(ForeignKey("words.id", ondelete="CASCADE"), primary_key=True)
    sentence_id: Mapped[int] = mapped_column(ForeignKey("sentences.id", ondelete="CASCADE"), primary_key=True)

    word: Mapped[Word] = relationship(back_populates="sentence_links")
    sentence: Mapped[Sentence] = relationship(back_populates="word_links")


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    position: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    word_links: Mapped[list["GroupWord"]] = relationship(
        back_populates="group",
        cascade="all, delete-orphan",
        order_by="GroupWord.position",
    )


class GroupWord(Base):
    __tablename__ = "group_words"

    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True)
    word_id: Mapped[int] = mapped_column(ForeignKey("words.id", ondelete="CASCADE"), primary_key=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False, primary_key=True)

    group: Mapped[Group] = relationship(back_populates="word_links")
    word: Mapped[Word] = relationship(back_populates="group_links")
