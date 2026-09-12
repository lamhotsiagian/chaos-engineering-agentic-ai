"""
Observability: Structured Contextual Logger for Agentic AI.

Outputs machine-parseable JSON logs embedded with OpenTelemetry trace contexts,
execution node names, resilience status, and failure metadata.
"""

import json
import logging
import sys
import time
from typing import Optional, Dict, Any


class JsonFormatter(logging.Formatter):
    """Formats log records as structured single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include structured context if passed via `extra`
        for key in ("trace_id", "run_id", "node", "model", "tool", "fault_type", "resilience_action"):
            if hasattr(record, key):
                log_data[key] = getattr(record, key)

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def setup_logger(name: str = "agent_chaos", level: int = logging.INFO) -> logging.Logger:
    """Configure and return a structured JSON logger."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers if called multiple times
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)

    return logger


# Global logger instance
logger = setup_logger()
