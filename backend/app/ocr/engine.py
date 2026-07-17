from __future__ import annotations

from io import BytesIO
import logging
import os
from threading import RLock
from typing import Any

from PIL import Image

from ..schemas.images import OcrBoxOut
from .parser import parse_paddle_result


logger = logging.getLogger(__name__)

# PaddlePaddle 3.3.x + PaddleOCR 3.x can fail on Windows CPU inference when
# PaddleX enables MKLDNN/oneDNN by default. This must be set before imports.
os.environ.setdefault("PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT", "0")


class OCREngineError(RuntimeError):
    pass


class OCREngine:
    def __init__(self, use_paddleocr: bool) -> None:
        self._use_paddleocr = use_paddleocr
        self._paddle: Any | None = None
        self._paddle_failed = False
        self._lock = RLock()

    def recognize(self, data: bytes, width: int, height: int) -> list[OcrBoxOut]:
        if not self._use_paddleocr:
            raise OCREngineError("Real OCR is disabled. Set USE_PADDLEOCR=true and install PaddleOCR.")
        return self._recognize_with_paddle(data, width, height)

    def _recognize_with_paddle(self, data: bytes, width: int, height: int) -> list[OcrBoxOut]:
        if self._paddle_failed:
            raise OCREngineError("PaddleOCR initialization failed earlier. Restart the backend after fixing it.")

        try:
            with self._lock:
                return self._recognize_with_paddle_locked(data, width, height)
        except ModuleNotFoundError as exc:
            self._paddle_failed = True
            logger.exception("ocr.paddle.dependencies_missing")
            raise OCREngineError("PaddleOCR dependencies are not installed.") from exc
        except Exception as exc:
            logger.exception("ocr.paddle.failed")
            raise OCREngineError(f"PaddleOCR failed: {exc}") from exc

    def _recognize_with_paddle_locked(self, data: bytes, width: int, height: int) -> list[OcrBoxOut]:
        if self._paddle is None:
            logger.info("ocr.paddle.init.start lang=ch")
            from paddleocr import PaddleOCR

            self._paddle = PaddleOCR(
                lang="ch",
                use_textline_orientation=True,
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                enable_mkldnn=False,
            )
            logger.info("ocr.paddle.init.finish")

        import numpy as np

        with Image.open(BytesIO(data)) as image:
            image = image.convert("RGB")
            image_array = np.array(image)

        logger.info("ocr.paddle.predict.start image_width=%s image_height=%s", width, height)
        raw_result = self._run_paddle_predict(image_array)
        logger.info("ocr.paddle.predict.finish result_type=%s", type(raw_result).__name__)

        boxes = parse_paddle_result(raw_result, width, height)
        logger.info("ocr.parse.finish boxes=%s", len(boxes))
        return boxes

    def _run_paddle_predict(self, image_array: Any) -> Any:
        if hasattr(self._paddle, "predict"):
            try:
                return self._paddle.predict(image_array, use_textline_orientation=True)
            except TypeError as exc:
                if "use_textline_orientation" not in str(exc):
                    raise
                logger.info("ocr.paddle.predict.retry_without_textline_orientation")
                return self._paddle.predict(image_array)
        return self._paddle.ocr(image_array, cls=True)
