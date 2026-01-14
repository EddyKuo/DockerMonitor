"""Tests for logger utilities."""

import pytest
import logging
from pathlib import Path
from src.utils.logger import setup_logger, get_logger, LoggerAdapter


def test_setup_logger():
    """Test logger setup."""
    logger = setup_logger(name="test_logger", level="DEBUG")

    assert logger is not None
    assert logger.name == "test_logger"
    assert logger.level == logging.DEBUG
    assert len(logger.handlers) > 0


def test_get_logger():
    """Test getting existing logger."""
    # Setup logger first
    setup_logger(name="test_get", level="INFO")

    # Get logger
    logger = get_logger("test_get")

    assert logger is not None
    assert logger.name == "test_get"


def test_logger_adapter():
    """Test logger adapter with context."""
    base_logger = setup_logger(name="test_adapter", level="DEBUG")

    adapter = LoggerAdapter(base_logger, {"host": "test-host", "port": 22})

    assert adapter is not None
    assert adapter.logger == base_logger
    assert adapter.context == {"host": "test-host", "port": 22}


def test_logger_adapter_format():
    """Test logger adapter message formatting."""
    base_logger = setup_logger(name="test_format", level="DEBUG")
    adapter = LoggerAdapter(base_logger, {"host": "host1"})

    formatted = adapter._format_message("Test message")

    assert "[host=host1]" in formatted
    assert "Test message" in formatted


def test_setup_logger_with_file(tmp_path):
    """Test logger with file output."""
    log_dir = tmp_path / "logs"
    log_file = "test.log"

    logger = setup_logger(
        name="test_file",
        level="INFO",
        log_file=log_file,
        log_dir=str(log_dir),
    )

    # Log a message
    logger.info("Test log message")

    # Check that log file was created
    log_path = log_dir / log_file
    assert log_path.exists()

    # Check log content
    content = log_path.read_text()
    assert "Test log message" in content


def test_logger_levels():
    """Test different logging levels."""
    logger = setup_logger(name="test_levels", level="DEBUG")

    # All these should work without errors
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")
