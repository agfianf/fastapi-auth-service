import time

import structlog

from fastapi import Request

from app.helpers.generator import generate_uuid


logger = structlog.get_logger(__name__)
EXCLUDED_PATHS = {"/", "/health"}


async def logging_middleware(request: Request, call_next):  # noqa: ANN001, ANN201
    """Middleware to add request context to logs."""
    if request.url.path in EXCLUDED_PATHS:
        return await call_next(request)

    request_id = str(generate_uuid())

    # Extract client IP (handles proxy headers like X-Forwarded-For, X-Real-IP)
    client_ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    if not client_ip:
        client_ip = request.headers.get("x-real-ip", "")
    if not client_ip and request.client:
        client_ip = request.client.host
    if not client_ip:
        client_ip = "unknown"

    # Extract request metadata
    host = request.headers.get("host", "")
    referer = request.headers.get("referer", "")

    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        path=request.url.path,
        method=request.method,
        client_ip=client_ip,
        host=host,
        referer=referer,
    )

    start_time = time.time()

    try:
        response = await call_next(request)
        processing_time = time.time() - start_time

        structlog.contextvars.bind_contextvars(
            status_code=response.status_code,
            processing_time_ms=round(processing_time * 1000, 2),
            response_content_length=response.headers.get("content-length", ""),
        )

        logger.info("Request completed successfully")
        return response
    except Exception as e:
        processing_time = time.time() - start_time
        structlog.contextvars.bind_contextvars(
            processing_time_ms=round(processing_time * 1000, 2),
            error_type=type(e).__name__,
        )
        logger.error("Request failed", error=str(e))
        raise
    finally:
        structlog.contextvars.unbind_contextvars(
            "request_id",
            "path",
            "method",
            "client_ip",
            "host",
            "referer",
            "user_id",
            "user_role",
            "status_code",
            "processing_time_ms",
            "response_content_length",
            "error_type",
        )
