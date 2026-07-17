from datetime import date, datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..constants import DEFAULT_USER_ID
from ..models import Note
from ..repositories import notes as notes_repo
from ..schemas.notes import NoteDeleteResult, NoteOut, NoteUpsert, NoteUpsertDeleted


def parse_note_date(raw_date: str) -> date:
    try:
        return date.fromisoformat(raw_date)
    except ValueError:
        raise HTTPException(status_code=422, detail="Date must be in YYYY-MM-DD format") from None


def serialize_note(note: Note) -> NoteOut:
    return NoteOut(
        id=note.id,
        note_date=note.note_date.isoformat(),
        text=note.text,
        created_at=note.created_at.isoformat() if note.created_at else None,
        updated_at=note.updated_at.isoformat() if note.updated_at else None,
    )


def list_notes(db: Session) -> list[NoteOut]:
    return [serialize_note(note) for note in notes_repo.list_notes(db, DEFAULT_USER_ID)]


def upsert_note(db: Session, raw_date: str, payload: NoteUpsert) -> NoteOut | NoteUpsertDeleted:
    parsed_date = parse_note_date(raw_date)
    raw_text = payload.text or ""

    note = notes_repo.get_by_date(db, DEFAULT_USER_ID, parsed_date)

    # Инвариант доски заметок: пустой текст означает удаление.
    if not raw_text.strip():
        if note is not None:
            notes_repo.delete(db, note)
            db.commit()
        return NoteUpsertDeleted(note_date=parsed_date.isoformat(), text="", deleted=True)

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if note is None:
        note = Note(user_id=DEFAULT_USER_ID, note_date=parsed_date, text=raw_text, created_at=now)
        notes_repo.add(db, note)

    note.text = raw_text
    note.updated_at = now
    db.commit()
    db.refresh(note)
    return serialize_note(note)


def delete_note(db: Session, raw_date: str) -> NoteDeleteResult:
    parsed_date = parse_note_date(raw_date)
    note = notes_repo.get_by_date(db, DEFAULT_USER_ID, parsed_date)

    if note is not None:
        notes_repo.delete(db, note)
        db.commit()

    return NoteDeleteResult(note_date=parsed_date.isoformat(), deleted=True)
