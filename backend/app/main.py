from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import get_settings

BACKEND_DIR = Path(__file__).resolve().parents[1]
PHOTO_STORAGE_DIR = BACKEND_DIR / "static" / "photos"


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Hanzi Learn API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    PHOTO_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    app.mount("/api/photo-files", StaticFiles(directory=PHOTO_STORAGE_DIR), name="photo-files")

    @app.get("/")
    def root() -> dict:
        return {"status": "ok"}

    @app.get("/api/health")
    def health() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
