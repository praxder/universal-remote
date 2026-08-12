"""File logging for caught errors, so suppressing the terminal dump stays debuggable."""

from __future__ import annotations

import logging
import os
from pathlib import Path

_LOGGER_NAME = "universal_remote"


def default_log_path() -> Path:
    """`$XDG_CONFIG_HOME/universal-remote/error.log`, falling back to ~/.config."""
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / "universal-remote" / "error.log"


def log_exception(error: BaseException, path: Path | None = None) -> None:
    """Append the exception's type, message, and full traceback to the log file."""
    target = path or default_log_path()
    _logger(target).error("%s: %s", type(error).__name__, error, exc_info=error)


def _logger(path: Path) -> logging.Logger:
    # A logger per resolved path, so distinct targets never share (or stack) handlers.
    logger = logging.getLogger(f"{_LOGGER_NAME}:{path}")
    if not logger.handlers:
        logger.setLevel(logging.ERROR)
        logger.propagate = False
        path.parent.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(path)
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)
    return logger
