from sqlalchemy.orm import Session

from ..schemas.data import LearningDataOut
from . import catalog
from .words import list_words


def get_learning_data(db: Session) -> LearningDataOut:
    return LearningDataOut(
        words=list_words(db),
        sentences=catalog.list_sentences(db),
        groups=catalog.list_groups(db),
        characters=catalog.list_characters(db),
        word_characters=catalog.list_word_characters(db),
    )
