from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Note


def list_notes(db: Session, user_id: str) -> list[Note]:
    return list(
        db.scalars(select(Note).where(Note.user_id == user_id).order_by(Note.note_date))
    )


def get_by_date(db: Session, user_id: str, note_date: date) -> Note | None:
    return db.scalars(
        select(Note).where(Note.user_id == user_id, Note.note_date == note_date)
    ).first()


def add(db: Session, note: Note) -> None:
    db.add(note)


def delete(db: Session, note: Note) -> None:
    db.delete(note)
