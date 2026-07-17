from __future__ import annotations

import logging
import time
from uuid import uuid4

from fastapi import Request


logger = logging.getLogger(__name__)


async def log_requests(request: Request, call_next):
    request_id = uuid4().hex[:8]
    started_at = time.perf_counter()
    client = request.client.host if request.client else "-"
    logger.info(
        "request.start id=%s method=%s path=%s client=%s",
        request_id,
        request.method,
        request.url.path,
        client,
    )
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = (time.perf_counter() - started_at) * 1000
        logger.exception(
            "request.error id=%s method=%s path=%s duration_ms=%.1f",
            request_id,
            request.method,
            request.url.path,
            duration_ms,
        )
        raise

    duration_ms = (time.perf_counter() - started_at) * 1000
    logger.info(
        "request.finish id=%s method=%s path=%s status=%s duration_ms=%.1f",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response
