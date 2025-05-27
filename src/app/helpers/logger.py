# logger_config.py
import logging
import os

from collections import OrderedDict
from logging.handlers import RotatingFileHandler

import structlog

from app.config import settings


def _reorder_keys(logger, method_name, event_dict):  # noqa: ANN001, ANN202, ARG001
    key_order = [
        "level",
        "event",
        "timestamp",
        "request_id",
        "method",
        "path",
        "status_code",
        "user_id",
        "user_role",
        "extra_field",
        "exception",
        "func_name",
        "logger",
        "pathname",
        "lineno",
        # "module",
        # "filename",
        # "thread",
        # "thread_name",
        # "process",
        # "process_name",
    ]
    ordered_event_dict = OrderedDict()
    for key in key_order:
        if key in event_dict:
            ordered_event_dict[key] = event_dict.pop(key)
    ordered_event_dict.update(event_dict)
    return ordered_event_dict


def setup_logging(
    log_file: str = "app.log",
    log_level: str = "INFO",
    is_async: bool = True,
    enable_json_logs: bool = True,  # noqa: ARG001
    enable_file_logs: bool = True,
) -> None:
    """Set up logging configuration for FastAPI application."""
    os.makedirs("logs", exist_ok=True)
    # Setup processors
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False),
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.CallsiteParameterAdder(
            {
                structlog.processors.CallsiteParameter.MODULE,
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.PATHNAME,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
                # structlog.processors.CallsiteParameter.THREAD,
                # structlog.processors.CallsiteParameter.THREAD_NAME,
                # structlog.processors.CallsiteParameter.PROCESS,
                # structlog.processors.CallsiteParameter.PROCESS_NAME,
            },
        ),
        structlog.stdlib.ExtraAdder(),
        _reorder_keys,
    ]

    type_bound_logger = structlog.stdlib.AsyncBoundLogger if is_async else structlog.stdlib.BoundLogger
    structlog.configure(
        processors=shared_processors
        + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        # call log with await syntax in thread pool executor
        wrapper_class=type_bound_logger,
        cache_logger_on_first_use=True,
    )

    renderer = structlog.dev.ConsoleRenderer() if settings.APP_DEBUG else structlog.processors.JSONRenderer()

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    # Setup handlers
    handlers: list[logging.Handler] = []

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    handlers.append(console_handler)

    # File handler (optional)
    if enable_file_logs:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
        )
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.handlers = []  # Remove existing handlers
    for handler in handlers:
        root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, log_level.upper()))

    logging.getLogger("multipart.multipart").setLevel(logging.WARNING)
    logging.getLogger("python_multipart.multipart").setLevel(logging.WARNING)
    logging.getLogger("passlib.handlers.argon2").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    # Uvicorn specific loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)

    # Database related (jika pakai)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("alembic").setLevel(logging.WARNING)

    # Setup uvicorn access logger
    logging.getLogger("uvicorn.access").handlers = handlers
    logging.getLogger("uvicorn.access").propagate = False

    # Setup fastapi logger
    logging.getLogger("fastapi").handlers = handlers
    logging.getLogger("fastapi").propagate = False
