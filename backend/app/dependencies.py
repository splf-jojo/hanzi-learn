from __future__ import annotations

import logging

from .clip_service import ClipImageEmbedder
from .config import get_settings
from .logging_config import configure_logging
from .ocr import OCREngine
from .pending_uploads import PendingUploadStore


settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger(__name__)

logger.info(
    "settings.loaded dotenv_path=%s use_paddleocr=%s clip_model=%s clip_pretrained=%s clip_device=%s",
    settings.dotenv_path,
    settings.use_paddleocr,
    settings.clip_model_name,
    settings.clip_pretrained,
    settings.clip_device,
)

ocr_engine = OCREngine(use_paddleocr=settings.use_paddleocr)
clip_embedder = ClipImageEmbedder(settings)
pending_uploads = PendingUploadStore()
