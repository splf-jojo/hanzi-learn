from functools import lru_cache
import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]
DOTENV_PATH = BACKEND_DIR / ".env"
load_dotenv(DOTENV_PATH, override=True)

DEFAULT_DATABASE_URL = "postgresql+psycopg://postgres:123@localhost:5432/hanzi"


def env_str(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name, default)
    if value is None:
        return None
    value = value.strip().strip('"').strip("'")
    return value or None


class Settings:
    def __init__(self) -> None:
        self.dotenv_path = DOTENV_PATH
        self.log_level = env_str("LOG_LEVEL", "INFO").upper()
        self.database_url = env_str("DATABASE_URL", DEFAULT_DATABASE_URL)

        self.max_image_mb = int(env_str("MAX_IMAGE_MB", "10"))
        self.max_image_bytes = self.max_image_mb * 1024 * 1024
        self.max_image_pixels = int(env_str("MAX_IMAGE_PIXELS", "24000000"))
        self.use_paddleocr = env_str("USE_PADDLEOCR", "true").lower() == "true"

        self.clip_model_name = env_str("CLIP_MODEL_NAME", "ViT-B-32")
        self.clip_pretrained = env_str("CLIP_PRETRAINED", "laion2b_s34b_b79k")
        self.clip_device = env_str("CLIP_DEVICE", "cpu")
        self.clip_embedding_dim = 512

        raw_origins = env_str(
            "CORS_ORIGINS",
            "http://localhost:5174,http://127.0.0.1:5174",
        )
        self.cors_origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
