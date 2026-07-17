from datetime import date, datetime

import pytest
from fastapi import HTTPException

from app.constants import DEFAULT_USER_ID
from app.models import Note
from app.repositories import notes as notes_repo
from app.schemas.notes import NoteDeleteResult, NoteOut, NoteUpsert, NoteUpsertDeleted
from app.services import notes as notes_service

OLD_TS = datetime(2020, 1, 1)


def test_upsert_creates_then_updates(db):
    created = notes_service.upsert_note(db, "2026-01-05", NoteUpsert(text="first"))
    assert isinstance(created, NoteOut)
    assert created.note_date == "2026-01-05"
    assert created.text == "first"
    assert created.created_at is not None
    assert created.updated_at == created.created_at

    # Отматываем метки назад, чтобы сдвиг updated_at был детерминированным.
    note = notes_repo.get_by_date(db, DEFAULT_USER_ID, date(2026, 1, 5))
    note.created_at = OLD_TS
    note.updated_at = OLD_TS
    db.commit()

    updated = notes_service.upsert_note(db, "2026-01-05", NoteUpsert(text="second"))
    assert isinstance(updated, NoteOut)
    assert updated.id == created.id
    assert updated.text == "second"
    assert updated.created_at == OLD_TS.isoformat()
    assert datetime.fromisoformat(updated.updated_at) > OLD_TS


def test_list_notes_ordered_by_date_for_default_user(db):
    db.add_all(
        [
            Note(user_id=DEFAULT_USER_ID, note_date=date(2026, 3, 1), text="march"),
            Note(user_id=DEFAULT_USER_ID, note_date=date(2026, 1, 1), text="january"),
            Note(user_id="other", note_date=date(2026, 2, 1), text="foreign"),
            Note(user_id=DEFAULT_USER_ID, note_date=date(2026, 2, 1), text="february"),
        ]
    )
    db.commit()

    result = notes_service.list_notes(db)
    assert [note.note_date for note in result] == ["2026-01-01", "2026-02-01", "2026-03-01"]
    assert [note.text for note in result] == ["january", "february", "march"]
    assert all(note.created_at is None and note.updated_at is None for note in result)


@pytest.mark.parametrize("empty_text", [None, "", "   \n\t"])
def test_upsert_empty_text_deletes_existing_note(db, empty_text):
    db.add(Note(user_id=DEFAULT_USER_ID, note_date=date(2026, 1, 5), text="keep me"))
    db.commit()

    result = notes_service.upsert_note(db, "2026-01-05", NoteUpsert(text=empty_text))
    assert isinstance(result, NoteUpsertDeleted)
    assert result.note_date == "2026-01-05"
    assert result.text == ""
    assert result.deleted is True
    assert notes_repo.get_by_date(db, DEFAULT_USER_ID, date(2026, 1, 5)) is None


def test_upsert_empty_text_on_missing_note_returns_deleted(db):
    result = notes_service.upsert_note(db, "2026-01-05", NoteUpsert())
    assert isinstance(result, NoteUpsertDeleted)
    assert result.note_date == "2026-01-05"
    assert result.text == ""
    assert result.deleted is True


def test_delete_note_is_idempotent(db):
    db.add(Note(user_id=DEFAULT_USER_ID, note_date=date(2026, 1, 5), text="bye"))
    db.commit()

    first = notes_service.delete_note(db, "2026-01-05")
    assert isinstance(first, NoteDeleteResult)
    assert first.note_date == "2026-01-05"
    assert first.deleted is True
    assert notes_repo.get_by_date(db, DEFAULT_USER_ID, date(2026, 1, 5)) is None

    second = notes_service.delete_note(db, "2026-01-05")
    assert second.note_date == "2026-01-05"
    assert second.deleted is True


@pytest.mark.parametrize("raw_date", ["not-a-date", "2026-13-01", "05.01.2026"])
def test_bad_date_raises_422_for_all_ops(db, raw_date):
    for call in (
        lambda: notes_service.upsert_note(db, raw_date, NoteUpsert(text="hi")),
        lambda: notes_service.upsert_note(db, raw_date, NoteUpsert(text="")),
        lambda: notes_service.delete_note(db, raw_date),
    ):
        with pytest.raises(HTTPException) as exc_info:
            call()
        assert exc_info.value.status_code == 422
        assert exc_info.value.detail == "Date must be in YYYY-MM-DD format"
