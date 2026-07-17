from fastapi import APIRouter

from . import catalog, data, images, notes, photos, uploads, words

api_router = APIRouter()
api_router.include_router(words.router)
api_router.include_router(photos.router)
api_router.include_router(notes.router)
api_router.include_router(catalog.router)
api_router.include_router(data.router)
api_router.include_router(images.router)
api_router.include_router(uploads.router)
