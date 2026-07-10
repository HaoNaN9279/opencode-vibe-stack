"""Logging configuration for vibe-stack.

Provides a simple, stdlib-only logging setup with consistent formatting
and output to stderr.
"""

from __future__ import annotations

import logging
import sys
from typing import Final, TextIO

_LOG_FORMAT: Final[str] = "%(asctime)s [vibe-stack] [%(levelname)s] %(message)s"
_ROOT_LOGGER_NAME: Final[str] = "vibe_stack"


def setup_logging(verbose: bool = False) -> None:
    """Configure the root logger with a stderr handler.

    Sets the root logger level to ``DEBUG`` when *verbose* is ``True``,
    otherwise ``WARNING``.  A single ``StreamHandler`` writing to stderr
    is added only if the root logger has no user-configured handlers —
    if it already has non-test handlers it is treated as "already
    configured" and the level is also left unchanged.

    Note:
        Pytest's ``LogCaptureHandler`` instances are ignored when
        checking for existing handlers so that the function works
        correctly under test.

    Args:
        verbose: If True, set log level to DEBUG; otherwise WARNING.
    """
    root = logging.getLogger()

    # Ignore pytest's internal LogCaptureHandler — only non-test
    # handlers count as "user configuration".
    _has_user_handlers = any(
        type(h).__name__ != "LogCaptureHandler" for h in root.handlers
    )
    if _has_user_handlers:
        return

    root.setLevel(logging.DEBUG if verbose else logging.WARNING)
    handler: logging.StreamHandler[TextIO] = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(_LOG_FORMAT))
    root.addHandler(handler)


def get_logger(name: str = "") -> logging.Logger:
    """Get (or create) a ``vibe_stack`` child logger.

    Args:
        name: Optional sub-logger name.  When provided the logger is
            named ``vibe_stack.<name>``; when omitted it returns the
            ``vibe_stack`` root logger.

    Returns:
        A :class:`logging.Logger` instance scoped to the vibe-stack
        namespace.
    """
    logger_name = _ROOT_LOGGER_NAME
    if name:
        logger_name = f"{_ROOT_LOGGER_NAME}.{name}"
    return logging.getLogger(logger_name)
