from __future__ import annotations

from argparse import ArgumentParser
from dataclasses import dataclass
from pathlib import Path
import logging
import os
import shutil

import chromadb
from dotenv import load_dotenv
from openai import APIConnectionError, APIStatusError, AuthenticationError, OpenAI


LOG_FORMAT = "%(levelname)s | %(message)s"
BACKEND_DIR = Path(__file__).resolve().parent
ENV_PATH = BACKEND_DIR / ".env"
load_dotenv(ENV_PATH, override=True)
DB_DIR = BACKEND_DIR / "chroma_db"
COLLECTION_NAME = "hanzi_openai_vectors"
EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
VECTOR_PREVIEW_SIZE = 8


@dataclass(frozen=True)
class HanziItem:
    hanzi: str
    pinyin: str
    meaning: str


HANZI_ITEMS: list[HanziItem] = [
    HanziItem("我", "wo3", "I, me"),
    HanziItem("你", "ni3", "you"),
    HanziItem("他", "ta1", "he"),
    HanziItem("她", "ta1", "she"),
    HanziItem("人", "ren2", "person"),
    HanziItem("家", "jia1", "home, family"),
    HanziItem("学", "xue2", "study"),
    HanziItem("书", "shu1", "book"),
    HanziItem("水", "shui3", "water"),
    HanziItem("火", "huo3", "fire"),
    HanziItem("山", "shan1", "mountain"),
    HanziItem("木", "mu4", "wood, tree"),
    HanziItem("日", "ri4", "sun, day"),
    HanziItem("月", "yue4", "moon, month"),
    HanziItem("口", "kou3", "mouth"),
    HanziItem("心", "xin1", "heart"),
    HanziItem("手", "shou3", "hand"),
    HanziItem("车", "che1", "car"),
    HanziItem("马", "ma3", "horse"),
    HanziItem("门", "men2", "door"),
]


def configure_logs() -> None:
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)


def load_environment() -> None:
    load_dotenv(ENV_PATH, override=True)


def get_openai_client() -> OpenAI:
    load_environment()
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is missing. Add it to backend/.env")

    return OpenAI(api_key=api_key)


def get_chroma_client():
    DB_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(DB_DIR))


def get_collection():
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={
            "hnsw:space": "cosine",
            "embedding_provider": "openai",
            "embedding_model": EMBEDDING_MODEL,
        },
    )


def reset_chroma_db() -> None:
    if DB_DIR.exists():
        shutil.rmtree(DB_DIR)

    DB_DIR.mkdir(parents=True, exist_ok=True)


def embedding_text(item: HanziItem) -> str:
    return f"{item.hanzi}\npinyin: {item.pinyin}\nmeaning: {item.meaning}"


def find_hanzi_item(hanzi: str) -> HanziItem | None:
    for item in HANZI_ITEMS:
        if item.hanzi == hanzi:
            return item

    return None


def query_text(hanzi: str) -> str:
    item = find_hanzi_item(hanzi)
    if item:
        return embedding_text(item)

    return hanzi


def vector_preview(vector: list[float]) -> str:
    preview = [round(value, 6) for value in vector[:VECTOR_PREVIEW_SIZE]]
    return f"dim={len(vector)} first_{VECTOR_PREVIEW_SIZE}={preview}"


def create_embeddings(texts: list[str]) -> list[list[float]]:
    client = get_openai_client()
    try:
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=texts,
            encoding_format="float",
        )
    except AuthenticationError as error:
        raise RuntimeError("OpenAI authentication failed. Check OPENAI_API_KEY in backend/.env") from error
    except APIConnectionError as error:
        raise RuntimeError("Could not connect to OpenAI. Check your network connection.") from error
    except APIStatusError as error:
        raise RuntimeError(f"OpenAI embeddings request failed with status {error.status_code}") from error

    embeddings_by_index = sorted(response.data, key=lambda item: item.index)
    return [item.embedding for item in embeddings_by_index]


def seed_openai_hanzi_vectors(reset: bool = True) -> None:
    embeddings = create_embeddings([embedding_text(item) for item in HANZI_ITEMS])

    if reset:
        reset_chroma_db()

    collection = get_collection()

    collection.upsert(
        ids=[item.hanzi for item in HANZI_ITEMS],
        documents=[item.hanzi for item in HANZI_ITEMS],
        embeddings=embeddings,
        metadatas=[
            {
                "hanzi": item.hanzi,
                "pinyin": item.pinyin,
                "meaning": item.meaning,
                "embedding_model": EMBEDDING_MODEL,
            }
            for item in HANZI_ITEMS
        ],
    )

    logging.info("Inserted %s OpenAI vectors into %s", len(HANZI_ITEMS), DB_DIR)
    logging.info("Embedding model: %s", EMBEDDING_MODEL)

    for item, vector in zip(HANZI_ITEMS, embeddings):
        logging.info(
            "%s %-5s %-14s vector=%s",
            item.hanzi,
            item.pinyin,
            item.meaning,
            vector_preview(vector),
        )


def collection_needs_seed() -> bool:
    collection = get_collection()
    metadata = collection.metadata or {}

    if collection.count() != len(HANZI_ITEMS):
        return True

    return metadata.get("embedding_model") != EMBEDDING_MODEL


def similarite(hanzi: str, top_k: int = 5) -> list[dict]:
    if collection_needs_seed():
        seed_openai_hanzi_vectors(reset=True)

    collection = get_collection()
    query_embedding = create_embeddings([query_text(hanzi)])[0]
    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    matches: list[dict] = []
    for document, metadata, distance in zip(
        result["documents"][0],
        result["metadatas"][0],
        result["distances"][0],
    ):
        matches.append(
            {
                "hanzi": document,
                "pinyin": metadata["pinyin"],
                "meaning": metadata["meaning"],
                "distance": round(distance, 6),
            }
        )

    return matches


def print_similarite(hanzi: str, top_k: int = 5) -> None:
    logging.info("Top %s similar hanzi for %s:", top_k, hanzi)
    for index, match in enumerate(similarite(hanzi, top_k), start=1):
        logging.info(
            "%s. %s %-5s %-14s distance=%s",
            index,
            match["hanzi"],
            match["pinyin"],
            match["meaning"],
            match["distance"],
        )


def main() -> None:
    parser = ArgumentParser(description="Seed ChromaDB with OpenAI hanzi embeddings and query similar hanzi.")
    parser.add_argument("hanzi", nargs="?", default="我", help="Chinese character to search. Example: 我")
    parser.add_argument("--top-k", type=int, default=5, help="How many similar items to return.")
    parser.add_argument("--no-reset", action="store_true", help="Keep the existing Chroma collection before upsert.")
    args = parser.parse_args()

    configure_logs()
    try:
        seed_openai_hanzi_vectors(reset=not args.no_reset)
        print_similarite(args.hanzi, top_k=args.top_k)
    except RuntimeError as error:
        logging.error("%s", error)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
