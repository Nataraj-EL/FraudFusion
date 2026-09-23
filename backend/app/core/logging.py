import json
import logging
import sys
from typing import Any


class JSONFormatter(logging.Formatter):
    """Structured JSON log formatter for production and security auditing."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            log_obj.update(record.extra)
        return json.dumps(log_obj)


def setup_logging(level: str = "INFO", json_logs: bool = False) -> logging.Logger:
    """Configures application-wide logging."""
    logger = logging.getLogger("fraud_fusion")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    if json_logs:
        handler.setFormatter(JSONFormatter())
    else:
        fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        handler.setFormatter(logging.Formatter(fmt))

    logger.addHandler(handler)
    return logger


logger = setup_logging()
