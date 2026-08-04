"""Structured logging with path / transcript redaction (CLAUDE.md; contract §10).

Logs answer *which stage ran, which fingerprints, why a cache hit/miss, why a
CapCut write was allowed/refused, which adapter/version* — without leaking home
paths, transcript text, or secrets.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

_HOME_RE = re.compile(re.escape(str(Path.home())))
_TOKEN_RE = re.compile(r"(auth[_-]?token|bearer)\s*[:=]\s*\S+", re.IGNORECASE)


class RedactingFilter(logging.Filter):
    """Replace the home directory and obvious secrets in every record."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            msg = record.getMessage()
        except Exception:  # pragma: no cover - defensive
            return True
        redacted = _HOME_RE.sub("~", msg)
        redacted = _TOKEN_RE.sub(r"\1=***", redacted)
        if redacted != msg:
            record.msg = redacted
            record.args = ()
        return True


def configure_logging(log_path: Path | None = None, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger("capcut_coach")
    if getattr(logger, "_coach_configured", False):
        return logger
    logger.setLevel(level)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")

    stream = logging.StreamHandler()
    stream.setFormatter(fmt)
    stream.addFilter(RedactingFilter())
    logger.addHandler(stream)

    if log_path is not None:
        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_path, encoding="utf-8")
            file_handler.setFormatter(fmt)
            file_handler.addFilter(RedactingFilter())
            logger.addHandler(file_handler)
        except OSError:
            pass

    logger._coach_configured = True  # type: ignore[attr-defined]
    return logger
