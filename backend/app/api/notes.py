from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.notes import NoteDeleteResult, NoteOut, NoteUpsert, NoteUpsertDeleted
from ..services import notes as notes_service

router = APIRouter(prefix="/api", tags=["notes"])


@router.get("/notes", response_model=list[NoteOut])
def list_notes(db: Session = Depends(get_db)) -> list[NoteOut]:
    return notes_service.list_notes(db)


@router.put("/notes/{note_date}", response_model=NoteOut | NoteUpsertDeleted)
def upsert_note(
    note_date: str, payload: NoteUpsert, db: Session = Depends(get_db)
) -> NoteOut | NoteUpsertDeleted:
    return notes_service.upsert_note(db, note_date, payload)


@router.delete("/notes/{note_date}", response_model=NoteDeleteResult)
def delete_note(note_date: str, db: Session = Depends(get_db)) -> NoteDeleteResult:
    return notes_service.delete_note(db, note_date)
