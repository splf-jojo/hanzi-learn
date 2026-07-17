from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.progress import UserWordProgress


def progress_map(db: Session, user_id: str) -> dict[int, int]:
    rows = db.scalars(select(UserWordProgress).where(UserWordProgress.user_id == user_id))
    return {row.word_id: row.knowledge_level for row in rows}


def get_or_create_progress(db: Session, user_id: str, word_id: int) -> UserWordProgress:
    progress = db.get(UserWordProgress, (user_id, word_id))
    if progress is None:
        progress = UserWordProgress(user_id=user_id, word_id=word_id)
        db.add(progress)
    return progress
