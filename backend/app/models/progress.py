from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base
from .learning import Character, Word


class UserWordProgress(Base):
    __tablename__ = "user_word_progress"

    user_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    word_id: Mapped[int] = mapped_column(ForeignKey("words.id", ondelete="CASCADE"), primary_key=True)
    knowledge_level: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    next_review_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    word: Mapped["Word"] = relationship(back_populates="progress_entries")


class UserCharacterProgress(Base):
    __tablename__ = "user_character_progress"

    user_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    character_id: Mapped[int] = mapped_column(ForeignKey("characters.id", ondelete="CASCADE"), primary_key=True)
    knowledge_level: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    next_review_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    character: Mapped["Character"] = relationship(back_populates="progress_entries")
