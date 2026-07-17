from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .api import api_router
from .config import get_settings
from .database import SessionLocal
from .logging_config import configure_logging
from .request_logging import log_requests
from .services.character_sync import sync_characters_from_words

BACKEND_DIR = Path(__file__).resolve().parents[1]
PHOTO_STORAGE_DIR = BACKEND_DIR / "static" / "photos"


@asynccontextmanager
async def lifespan(app: FastAPI):
    with SessionLocal() as db:
        sync_characters_from_words(db)
        db.commit()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(title="Hanzi Learn API", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.middleware("http")(log_requests)

    PHOTO_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    app.mount("/api/photo-files", StaticFiles(directory=PHOTO_STORAGE_DIR), name="photo-files")

    app.include_router(api_router)

    @app.get("/")
    def root() -> dict:
        return {"status": "ok"}

    @app.get("/api/health")
    def health() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
