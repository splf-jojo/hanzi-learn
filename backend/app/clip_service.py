from __future__ import annotations

from io import BytesIO
import logging
from threading import RLock
from typing import Any

from PIL import Image

from .config import Settings


logger = logging.getLogger(__name__)


class ImageEmbeddingError(RuntimeError):
    pass


class ClipImageEmbedder:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._lock = RLock()
        self._model: Any | None = None
        self._preprocess: Any | None = None
        self._torch: Any | None = None

    def embed_image(self, image_bytes: bytes) -> list[float]:
        try:
            self._ensure_loaded()
            with Image.open(BytesIO(image_bytes)) as image:
                image = image.convert("RGB")
                tensor = self._preprocess(image).unsqueeze(0).to(self._settings.clip_device)

            with self._torch.no_grad():
                features = self._model.encode_image(tensor)
                features = features / features.norm(dim=-1, keepdim=True)

            embedding = features.squeeze(0).detach().cpu().float().numpy().tolist()
        except Exception as exc:
            logger.exception("clip.embedding.failed")
            raise ImageEmbeddingError(str(exc)) from exc

        if len(embedding) != self._settings.clip_embedding_dim:
            raise ImageEmbeddingError(
                f"Expected {self._settings.clip_embedding_dim}-dimensional CLIP embedding, got {len(embedding)}."
            )
        return [float(value) for value in embedding]

    def _ensure_loaded(self) -> None:
        if self._model is not None and self._preprocess is not None:
            return

        with self._lock:
            if self._model is not None and self._preprocess is not None:
                return

            logger.info(
                "clip.load.start model=%s pretrained=%s device=%s",
                self._settings.clip_model_name,
                self._settings.clip_pretrained,
                self._settings.clip_device,
            )
            import open_clip
            import torch

            model, _, preprocess = open_clip.create_model_and_transforms(
                self._settings.clip_model_name,
                pretrained=self._settings.clip_pretrained,
                device=self._settings.clip_device,
            )
            model.eval()
            self._model = model
            self._preprocess = preprocess
            self._torch = torch
            logger.info("clip.load.finish")
