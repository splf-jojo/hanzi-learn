from pydantic import BaseModel


class NoteUpsert(BaseModel):
    text: str | None = None


class NoteOut(BaseModel):
    id: int
    note_date: str
    text: str
    created_at: str | None
    updated_at: str | None


class NoteUpsertDeleted(BaseModel):
    """Ответ PUT при пустом тексте: заметка удалена (инвариант доски)."""

    note_date: str
    text: str = ""
    deleted: bool = True


class NoteDeleteResult(BaseModel):
    note_date: str
    deleted: bool = True
