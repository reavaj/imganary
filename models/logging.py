import json
import logging
import sys
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    def __init__(self, service_name: str):
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        log_object = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "severity": record.levelname,
            "service": self.service_name,
            "message": record.getMessage(),
        }
        if hasattr(record, "props"):
            log_object.update(record.props)
        if record.exc_info:
            log_object["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_object)


def get_logger(service_name: str, level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger(service_name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter(service_name=service_name))
        logger.addHandler(handler)
        # Only set level if not already configured (allows CLI to pre-set level)
        if logger.level == logging.NOTSET:
            logger.setLevel(level.upper())
        logger.propagate = False
    return logger
