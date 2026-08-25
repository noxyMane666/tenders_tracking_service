import logging
import logging.config
import os
from contextvars import ContextVar
from datetime import datetime, timezone

REQUEST_ID_CTX: ContextVar[str] = ContextVar("request_id", default="-")
REQUEST_METHOD_CTX: ContextVar[str] = ContextVar("request_method", default="-")
REQUEST_PATH_CTX: ContextVar[str] = ContextVar("request_path", default="-")

RESERVED_LOG_RECORD_KEYS = set(logging.makeLogRecord({}).__dict__.keys()) | {"message", "asctime"}


def _normalize_extra_key(key: str) -> str:
    normalized = key
    while normalized in RESERVED_LOG_RECORD_KEYS:
        normalized = f"extra_{normalized}"
    return normalized


class SafeExtraLogger(logging.Logger):
    """Renames `extra` keys that collide with reserved LogRecord attributes
    instead of crashing the log call."""

    def makeRecord(
            self,
            name: str,
            level: int,
            fn: str,
            lno: int,
            msg,
            args,
            exc_info,
            func=None,
            extra=None,
            sinfo=None,
    ) -> logging.LogRecord:
        if extra:
            extra = {_normalize_extra_key(str(key)): value for key, value in extra.items()}
        return super().makeRecord(name, level, fn, lno, msg, args, exc_info, func, extra, sinfo)


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = REQUEST_ID_CTX.get()
        record.request_method = REQUEST_METHOD_CTX.get()
        record.request_path = REQUEST_PATH_CTX.get()
        return True


class CompactFormatter(logging.Formatter):
    """One-line log format: timestamp, level, message, request context, extras."""

    DISPLAY_ORDER_KEYS = ("event", "status_code", "tender_id", "duration_ms", "total")
    HIDDEN_KEYS = RESERVED_LOG_RECORD_KEYS | {
        "request_id",
        "request_method",
        "request_path",
        "taskName",
        "color_message",
    }

    @staticmethod
    def _to_text(value) -> str:
        text = str(value)
        return f"{text[:237]}..." if len(text) > 240 else text

    def format(self, record: logging.LogRecord) -> str:
        ts = datetime.fromtimestamp(record.created, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        message = f"{ts} {record.levelname:<8} {record.name}: {record.getMessage()}"

        request_id = getattr(record, "request_id", "-")
        if request_id != "-":
            message = f"{message} [req={request_id}]"

        request_method = getattr(record, "request_method", "-")
        request_path = getattr(record, "request_path", "-")
        if request_method != "-" and request_path != "-":
            message = f"{message} [{request_method} {request_path}]"

        extras = {
            key: value
            for key, value in record.__dict__.items()
            if key not in self.HIDDEN_KEYS
        }

        meta = []
        for key in self.DISPLAY_ORDER_KEYS:
            if key in extras and extras[key] is not None:
                meta.append(f"{key}={self._to_text(extras.pop(key))}")
        for key in sorted(extras.keys()):
            if extras[key] is not None:
                meta.append(f"{key}={self._to_text(extras[key])}")

        if meta:
            message = f"{message} | {' '.join(meta)}"
        if record.exc_info:
            message = f"{message}\n{self.formatException(record.exc_info)}"

        return message


def set_request_context(request_id: str, method: str, path: str) -> None:
    REQUEST_ID_CTX.set(request_id or "-")
    REQUEST_METHOD_CTX.set(method or "-")
    REQUEST_PATH_CTX.set(path or "-")


def clear_request_context() -> None:
    REQUEST_ID_CTX.set("-")
    REQUEST_METHOD_CTX.set("-")
    REQUEST_PATH_CTX.set("-")


def setup_logging() -> logging.Logger:
    logging.setLoggerClass(SafeExtraLogger)
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {"request_context": {"()": RequestContextFilter}},
        "formatters": {"compact": {"()": CompactFormatter}},
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "compact",
                "filters": ["request_context"],
                "stream": "ext://sys.stdout",
            }
        },
        "root": {"level": log_level, "handlers": ["console"]},
        "loggers": {
            "uvicorn": {"level": log_level, "handlers": ["console"], "propagate": False},
            "uvicorn.error": {"level": log_level, "handlers": ["console"], "propagate": False},
            "uvicorn.access": {"level": log_level, "handlers": ["console"], "propagate": False},
        },
    })

    logging.captureWarnings(True)
    return logging.getLogger()
