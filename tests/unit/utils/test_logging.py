"""Tests for vibe-stack logging utility."""

from __future__ import annotations

import io
import logging
import re
from collections.abc import Generator

import pytest

from vibe_stack.utils.logging import get_logger, setup_logging


class TestGetLogger:
    """Tests for get_logger()."""

    def test_returns_logger_instance(self) -> None:
        """get_logger should return a logging.Logger instance."""
        logger = get_logger("test")
        assert isinstance(logger, logging.Logger)

    def test_same_name_returns_same_instance(self) -> None:
        """get_logger with the same name should return the same logger instance."""
        logger_a = get_logger("same_name")
        logger_b = get_logger("same_name")
        assert logger_a is logger_b

    def test_default_name_is_vibe_stack(self) -> None:
        """get_logger with no arguments should return the 'vibe_stack' logger."""
        logger = get_logger()
        assert logger.name == "vibe_stack"

    def test_name_with_suffix(self) -> None:
        """get_logger with a name should create 'vibe_stack.<name>'."""
        logger = get_logger("mcp")
        assert logger.name == "vibe_stack.mcp"

    def test_different_names_different_instances(self) -> None:
        """get_logger with different names should return different logger instances."""
        logger_a = get_logger("alpha")
        logger_b = get_logger("beta")
        assert logger_a is not logger_b
        assert logger_a.name == "vibe_stack.alpha"
        assert logger_b.name == "vibe_stack.beta"


class TestSetupLogging:
    """Tests for setup_logging()."""

    @pytest.fixture(autouse=True)
    def _reset_root_logger(self) -> Generator[None, None, None]:
        """Reset the root logger's handlers and level before each test."""
        root = logging.getLogger()
        # Save and restore handlers
        old_handlers = root.handlers[:]
        old_level = root.level
        old_disabled = root.disabled
        root.handlers.clear()
        root.disabled = False
        yield
        root.handlers.clear()
        root.handlers.extend(old_handlers)
        root.setLevel(old_level)
        root.disabled = old_disabled

    def test_verbose_false_sets_warning(self) -> None:
        """setup_logging(verbose=False) should set root logger to WARNING."""
        setup_logging(verbose=False)
        root = logging.getLogger()
        assert root.level == logging.WARNING

    def test_verbose_true_sets_debug(self) -> None:
        """setup_logging(verbose=True) should set root logger to DEBUG."""
        setup_logging(verbose=True)
        root = logging.getLogger()
        assert root.level == logging.DEBUG

    def test_default_verbose_is_false(self) -> None:
        """setup_logging with no arguments should default to verbose=False."""
        setup_logging()
        root = logging.getLogger()
        assert root.level == logging.WARNING

    def test_output_goes_to_stderr(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Log output should go to stderr."""
        stream = io.StringIO()
        monkeypatch.setattr("sys.stderr", stream)

        setup_logging(verbose=True)
        logger = get_logger("test_stderr")
        logger.info("hello stderr")

        output = stream.getvalue()
        assert "hello stderr" in output

    def test_log_format_contains_timestamp_level_message(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Log format should contain timestamp, level, and message."""
        stream = io.StringIO()
        monkeypatch.setattr("sys.stderr", stream)

        setup_logging(verbose=True)
        logger = get_logger("test_format")
        logger.warning("format check")

        output = stream.getvalue()
        # Expected format: "2026-07-10 14:48:00,123 [vibe-stack] [WARNING] format check"
        assert re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", output), (
            f"Output should contain a timestamp, got: {output!r}"
        )
        assert "[vibe-stack]" in output, (
            f"Output should contain '[vibe-stack]', got: {output!r}"
        )
        assert "[WARNING]" in output or "[INFO]" in output, (
            f"Output should contain a level bracketed, got: {output!r}"
        )
        assert "format check" in output, (
            f"Output should contain the message, got: {output!r}"
        )

    def test_does_not_modify_root_logger_if_already_configured(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """setup_logging should not modify root logger if it already has handlers."""
        root = logging.getLogger()
        existing_handler = logging.StreamHandler(io.StringIO())
        root.addHandler(existing_handler)
        root.setLevel(logging.ERROR)
        original_handler_count = len(root.handlers)

        setup_logging(verbose=True)

        assert len(root.handlers) == original_handler_count
        assert root.level == logging.ERROR
