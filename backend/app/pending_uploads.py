from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from uuid import uuid4


@dataclass(frozen=True)
class PendingUpload:
    upload_id: str
    filename: str | None
    content_type: str
    image_bytes: bytes
    image_width: int
    image_height: int
    embedding: list[float]


class PendingUploadStore:
    def __init__(self) -> None:
        self._lock = RLock()
        self._uploads: dict[str, PendingUpload] = {}

    def create(
        self,
        filename: str | None,
        content_type: str,
        image_bytes: bytes,
        image_width: int,
        image_height: int,
        embedding: list[float],
    ) -> PendingUpload:
        upload = PendingUpload(
            upload_id=f"upl_{uuid4().hex[:12]}",
            filename=filename,
            content_type=content_type,
            image_bytes=image_bytes,
            image_width=image_width,
            image_height=image_height,
            embedding=embedding,
        )
        with self._lock:
            self._uploads[upload.upload_id] = upload
        return upload

    def get(self, upload_id: str) -> PendingUpload | None:
        with self._lock:
            return self._uploads.get(upload_id)

    def remove(self, upload_id: str) -> None:
        with self._lock:
            self._uploads.pop(upload_id, None)
