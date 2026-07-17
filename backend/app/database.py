from pathlib import Path
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker


BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:123@localhost:5432/chinese",
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def table_names() -> set[str]:
    return set(inspect(engine).get_table_names())


def column_names(table_name: str) -> set[str]:
    return {column["name"] for column in inspect(engine).get_columns(table_name)}


def execute_ddl(statement: str) -> None:
    with engine.begin() as connection:
        connection.execute(text(statement))


def rename_table_if_needed(old_name: str, new_name: str) -> None:
    names = table_names()
    if old_name in names and new_name not in names:
        execute_ddl(f"ALTER TABLE {old_name} RENAME TO {new_name}")


def rename_column_if_needed(table_name: str, old_name: str, new_name: str) -> None:
    if table_name not in table_names():
        return

    names = column_names(table_name)
    if old_name in names and new_name not in names:
        execute_ddl(f"ALTER TABLE {table_name} RENAME COLUMN {old_name} TO {new_name}")


def add_column_if_missing(table_name: str, column_name: str, column_type: str) -> None:
    if table_name not in table_names():
        return

    if column_name not in column_names(table_name):
        execute_ddl(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")


def drop_column_if_present(table_name: str, column_name: str) -> None:
    if table_name not in table_names():
        return

    if column_name in column_names(table_name):
        execute_ddl(f"ALTER TABLE {table_name} DROP COLUMN {column_name}")


def migrate_legacy_schema() -> None:
    rename_table_if_needed("gropups", "groups")
    rename_table_if_needed("gropup_words", "group_words")
    rename_column_if_needed("group_words", "gropup_id", "group_id")

    rename_column_if_needed("words", "term", "hanzi")
    rename_column_if_needed("words", "meaning", "translation")
    rename_column_if_needed("sentences", "sentence", "hanzi")
    rename_column_if_needed("characters", "meaning", "translation")

    add_column_if_missing("words", "description", "TEXT NOT NULL DEFAULT ''")
    add_column_if_missing("words", "part_of_speech", "VARCHAR(80) NOT NULL DEFAULT ''")
    add_column_if_missing("words", "level", "VARCHAR(40) NOT NULL DEFAULT ''")
    add_column_if_missing("words", "photo_id", "INTEGER NULL")
    add_column_if_missing("words", "position", "INTEGER NOT NULL DEFAULT 0")
    add_column_if_missing("words", "created_at", "TIMESTAMP NULL")
    add_column_if_missing("words", "updated_at", "TIMESTAMP NULL")

    add_column_if_missing("characters", "description", "TEXT NOT NULL DEFAULT ''")
    add_column_if_missing("characters", "radical", "VARCHAR(16) NOT NULL DEFAULT ''")
    add_column_if_missing("characters", "strokes", "INTEGER NULL")
    add_column_if_missing("characters", "hsk_level", "VARCHAR(40) NOT NULL DEFAULT ''")
    add_column_if_missing("characters", "position", "INTEGER NOT NULL DEFAULT 0")

    add_column_if_missing("sentences", "description", "TEXT NOT NULL DEFAULT ''")
    add_column_if_missing("sentences", "position", "INTEGER NOT NULL DEFAULT 0")
    add_column_if_missing("groups", "description", "TEXT NOT NULL DEFAULT ''")
    add_column_if_missing("groups", "position", "INTEGER NOT NULL DEFAULT 0")
    add_column_if_missing("group_words", "position", "INTEGER NOT NULL DEFAULT 0")

    add_column_if_missing("word_characters", "pinyin", "VARCHAR(160) NOT NULL DEFAULT ''")
    add_column_if_missing("word_characters", "role", "VARCHAR(80) NOT NULL DEFAULT ''")
    drop_column_if_present("words", "term")
    drop_column_if_present("words", "meaning")
    drop_column_if_present("characters", "meaning")
    drop_column_if_present("sentences", "sentence")
    drop_column_if_present("words", "number")
    drop_column_if_present("characters", "number")
    drop_column_if_present("sentences", "number")
    drop_column_if_present("groups", "number")
    drop_column_if_present("word_characters", "full_word")


def migrate_legacy_word_progress() -> None:
    if "words" not in table_names() or "user_word_progress" not in table_names():
        return

    if "knowledge_level" not in column_names("words"):
        return

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO user_word_progress (user_id, word_id, knowledge_level)
                SELECT 'local', id, knowledge_level
                FROM words
                WHERE knowledge_level IS NOT NULL
                ON CONFLICT DO NOTHING
                """
            )
        )

    drop_column_if_present("words", "knowledge_level")


def init_db():
    from . import models  # noqa: F401

    migrate_legacy_schema()
    Base.metadata.create_all(bind=engine)
    migrate_legacy_word_progress()
