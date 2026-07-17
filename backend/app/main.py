from contextlib import asynccontextmanager
from datetime import date, datetime, timezone
from pathlib import Path

from fastapi import Body, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .character_sync import sync_characters_from_words
from .database import SessionLocal, get_db, init_db
from .models import (
    Character,
    Group,
    Note,
    Photo,
    Sentence,
    UserWordProgress,
    Word,
    WordCharacter,
)

DEFAULT_USER_ID = "local"
BACKEND_DIR = Path(__file__).resolve().parents[1]
PHOTO_STORAGE_DIR = BACKEND_DIR / "static" / "photos"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    with SessionLocal() as db:
        sync_characters_from_words(db)
        db.commit()
    yield


app = FastAPI(title="Chinese Learning API", lifespan=lifespan)
PHOTO_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/api/photo-files", StaticFiles(directory=PHOTO_STORAGE_DIR), name="photo-files")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def normalize_knowledge_level(value) -> int:
    if isinstance(value, bool):
        raise ValueError

    try:
        level = int(value)
    except (TypeError, ValueError):
        raise ValueError from None

    if level < 0 or level > 5:
        raise ValueError

    return level


def word_progress_map(db: Session, user_id: str = DEFAULT_USER_ID) -> dict[int, int]:
    rows = db.scalars(select(UserWordProgress).where(UserWordProgress.user_id == user_id))
    return {row.word_id: row.knowledge_level for row in rows}


def serialize_word_character(link: WordCharacter) -> dict:
    return {
        "word_id": link.word_id,
        "character_id": link.character_id,
        "id": link.character_id,
        "glyph": link.character.glyph,
        "position": link.position,
        "pinyin": link.pinyin,
        "role": link.role,
    }


def serialize_word(word: Word, progress_by_word_id: dict[int, int] | None = None) -> dict:
    knowledge_level = (progress_by_word_id or {}).get(word.id, 0)

    return {
        "id": word.id,
        "hanzi": word.hanzi,
        "pinyin": word.pinyin,
        "translation": word.translation,
        "description": word.description,
        "part_of_speech": word.part_of_speech,
        "level": word.level,
        "photo_id": word.photo_id,
        "position": word.position,
        "knowledge_level": knowledge_level,
        "characters": [serialize_word_character(link) for link in word.character_links],
    }


def serialize_photo(photo: Photo) -> dict:
    return {
        "id": photo.id,
        "slug": photo.slug,
        "filename": photo.filename,
        "content_type": photo.content_type,
        "alt": photo.alt,
        "source": photo.source,
        "url": f"/api/photo-files/{photo.filename}",
    }


def serialize_character(character: Character) -> dict:
    return {
        "id": character.id,
        "glyph": character.glyph,
        "pinyin": character.pinyin,
        "translation": character.translation,
        "description": character.description,
        "radical": character.radical,
        "strokes": character.strokes,
        "hsk_level": character.hsk_level,
        "image": character.image,
        "position": character.position,
    }


def serialize_sentence(sentence: Sentence) -> dict:
    return {
        "id": sentence.id,
        "hanzi": sentence.hanzi,
        "pinyin": sentence.pinyin,
        "translation": sentence.translation,
        "description": sentence.description,
        "words": [link.word_id for link in sentence.word_links],
    }


def serialize_group(group: Group) -> dict:
    return {
        "id": group.id,
        "words": [link.word_id for link in group.word_links],
        "name": group.name,
        "description": group.description,
    }


def get_words(db: Session) -> list[Word]:
    return list(
        db.scalars(
            select(Word)
            .options(selectinload(Word.character_links).selectinload(WordCharacter.character))
            .order_by(Word.position, Word.id)
        )
    )


def get_photo_by_slug(db: Session, slug: str) -> Photo | None:
    return db.scalar(select(Photo).where(Photo.slug == slug))


def get_characters(db: Session) -> list[Character]:
    return list(db.scalars(select(Character).order_by(Character.position, Character.id)))


def get_word_characters(db: Session) -> list[WordCharacter]:
    return list(
        db.scalars(
            select(WordCharacter)
            .options(selectinload(WordCharacter.character))
            .order_by(WordCharacter.word_id, WordCharacter.position)
        )
    )


def get_sentences(db: Session) -> list[Sentence]:
    return list(
        db.scalars(
            select(Sentence)
            .options(selectinload(Sentence.word_links))
            .order_by(Sentence.position, Sentence.id)
        )
    )


def get_groups(db: Session) -> list[Group]:
    return list(
        db.scalars(
            select(Group)
            .options(selectinload(Group.word_links))
            .order_by(Group.position, Group.id)
        )
    )


@app.get("/")
def root() -> dict:
    return {"status": "ok"}


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/words")
def words(db: Session = Depends(get_db)) -> list[dict]:
    progress_by_word_id = word_progress_map(db)
    return [serialize_word(word, progress_by_word_id) for word in get_words(db)]


@app.get("/api/photos/{photo_id}")
def photo(photo_id: int, db: Session = Depends(get_db)) -> dict:
    photo_record = db.get(Photo, photo_id)
    if photo_record is None:
        raise HTTPException(status_code=404, detail="Photo not found")

    return serialize_photo(photo_record)


@app.get("/api/words/{word_id}/photo")
def word_photo(word_id: int, db: Session = Depends(get_db)) -> dict:
    word = db.get(Word, word_id)
    if word is None:
        raise HTTPException(status_code=404, detail="Word not found")

    if word.photo_id is None:
        raise HTTPException(status_code=404, detail="Word photo not found")

    photo_record = db.get(Photo, word.photo_id)
    if photo_record is None:
        raise HTTPException(status_code=404, detail="Photo not found")

    return serialize_photo(photo_record)


@app.patch("/api/words/{word_id}/photo")
def update_word_photo(word_id: int, payload: dict = Body(...), db: Session = Depends(get_db)) -> dict:
    word = db.get(Word, word_id)
    if word is None:
        raise HTTPException(status_code=404, detail="Word not found")

    if not isinstance(payload, dict):
        raise HTTPException(status_code=422, detail="Request body must be a JSON object")

    raw_photo_id = payload.get("photo_id", payload.get("photoId"))
    raw_photo_slug = payload.get("photo_slug", payload.get("photoSlug", payload.get("slug")))

    if raw_photo_id is None and raw_photo_slug is None:
        word.photo_id = None
        db.commit()
        return {"word_id": word.id, "photo": None}

    photo_record = None
    if raw_photo_id is not None:
        try:
            photo_id = int(raw_photo_id)
        except (TypeError, ValueError):
            raise HTTPException(status_code=422, detail="photo_id must be an integer") from None

        photo_record = db.get(Photo, photo_id)
    else:
        photo_record = get_photo_by_slug(db, str(raw_photo_slug))

    if photo_record is None:
        raise HTTPException(status_code=404, detail="Photo not found")

    word.photo_id = photo_record.id
    db.commit()
    return {"word_id": word.id, "photo": serialize_photo(photo_record)}


@app.patch("/api/words/{word_id}/knowledge-level")
@app.patch("/api/word-progress/{word_id}/knowledge-level")
def update_word_knowledge_level(word_id: int, payload: dict = Body(...), db: Session = Depends(get_db)) -> dict:
    word = db.get(Word, word_id)
    if word is None:
        raise HTTPException(status_code=404, detail="Word not found")

    if not isinstance(payload, dict):
        raise HTTPException(status_code=422, detail="Request body must be a JSON object")

    raw_level = payload.get("knowledge_level", payload.get("knowledgeLevel"))
    try:
        next_level = normalize_knowledge_level(raw_level)
    except ValueError:
        raise HTTPException(status_code=422, detail="knowledge_level must be an integer from 0 to 5") from None

    progress = db.get(UserWordProgress, (DEFAULT_USER_ID, word_id))
    if progress is None:
        progress = UserWordProgress(user_id=DEFAULT_USER_ID, word_id=word_id)
        db.add(progress)

    progress.knowledge_level = next_level
    db.commit()
    db.refresh(word)
    return serialize_word(word, {word_id: next_level})


def parse_note_date(raw_date: str) -> date:
    try:
        return date.fromisoformat(raw_date)
    except ValueError:
        raise HTTPException(status_code=422, detail="Date must be in YYYY-MM-DD format") from None


def serialize_note(note: Note) -> dict:
    return {
        "id": note.id,
        "note_date": note.note_date.isoformat(),
        "text": note.text,
        "created_at": note.created_at.isoformat() if note.created_at else None,
        "updated_at": note.updated_at.isoformat() if note.updated_at else None,
    }


def get_note_by_date(db: Session, note_date: date) -> Note | None:
    return db.scalars(
        select(Note).where(Note.user_id == DEFAULT_USER_ID, Note.note_date == note_date)
    ).first()


@app.get("/api/notes")
def notes(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.scalars(
        select(Note).where(Note.user_id == DEFAULT_USER_ID).order_by(Note.note_date)
    )
    return [serialize_note(note) for note in rows]


@app.put("/api/notes/{note_date}")
def upsert_note(note_date: str, payload: dict = Body(...), db: Session = Depends(get_db)) -> dict:
    parsed_date = parse_note_date(note_date)

    if not isinstance(payload, dict):
        raise HTTPException(status_code=422, detail="Request body must be a JSON object")

    raw_text = payload.get("text", "")
    if raw_text is None:
        raw_text = ""
    if not isinstance(raw_text, str):
        raise HTTPException(status_code=422, detail="text must be a string")

    note = get_note_by_date(db, parsed_date)

    if not raw_text.strip():
        if note is not None:
            db.delete(note)
            db.commit()
        return {"note_date": parsed_date.isoformat(), "text": "", "deleted": True}

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if note is None:
        note = Note(user_id=DEFAULT_USER_ID, note_date=parsed_date, text=raw_text, created_at=now)
        db.add(note)

    note.text = raw_text
    note.updated_at = now
    db.commit()
    db.refresh(note)
    return serialize_note(note)


@app.delete("/api/notes/{note_date}")
def delete_note(note_date: str, db: Session = Depends(get_db)) -> dict:
    parsed_date = parse_note_date(note_date)
    note = get_note_by_date(db, parsed_date)

    if note is not None:
        db.delete(note)
        db.commit()

    return {"note_date": parsed_date.isoformat(), "deleted": True}


@app.get("/api/sentences")
def sentences(db: Session = Depends(get_db)) -> list[dict]:
    return [serialize_sentence(sentence) for sentence in get_sentences(db)]


@app.get("/api/characters")
def characters(db: Session = Depends(get_db)) -> list[dict]:
    return [serialize_character(character) for character in get_characters(db)]


@app.get("/api/word-characters")
def word_characters(db: Session = Depends(get_db)) -> list[dict]:
    return [serialize_word_character(link) for link in get_word_characters(db)]


@app.get("/api/groups")
def groups(db: Session = Depends(get_db)) -> list[dict]:
    return [serialize_group(group) for group in get_groups(db)]


@app.get("/api/gropups")
def legacy_gropups(db: Session = Depends(get_db)) -> list[dict]:
    return groups(db)


@app.get("/api/data")
def data(db: Session = Depends(get_db)) -> dict:
    progress_by_word_id = word_progress_map(db)
    word_character_links = get_word_characters(db)
    serialized_groups = [serialize_group(group) for group in get_groups(db)]

    return {
        "words": [serialize_word(word, progress_by_word_id) for word in get_words(db)],
        "sentences": [serialize_sentence(sentence) for sentence in get_sentences(db)],
        "groups": serialized_groups,
        "gropups": serialized_groups,
        "characters": [serialize_character(character) for character in get_characters(db)],
        "word_characters": [serialize_word_character(link) for link in word_character_links],
    }
