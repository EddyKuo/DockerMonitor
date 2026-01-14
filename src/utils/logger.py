"""Logging configuration for DockerMonitor."""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


def setup_logger(
    name: str = "dockermonitor",
    level: str = "INFO",
    log_file: Optional[str] = None,
    log_dir: str = "logs",
    console_enabled: bool = True,
) -> logging.Logger:
    """
    Set up and configure logger.

    Args:
        name: Logger name.
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Optional log file name. If None, uses timestamp.
        log_dir: Directory to store log files.
        console_enabled: Whether to enable console logging. Set to False for TUI mode.

    Returns:
        Configured logger instance.
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Clear existing handlers
    logger.handlers.clear()

    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    simple_formatter = logging.Formatter(
        fmt="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
    )

    # Console handler (stdout) with auto-flush - disabled in TUI mode
    if console_enabled:
        class FlushingStreamHandler(logging.StreamHandler):
            def emit(self, record):
                super().emit(record)
                self.flush()

        console_handler = FlushingStreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG if level.upper() == "DEBUG" else logging.INFO)
        console_handler.setFormatter(simple_formatter)
        logger.addHandler(console_handler)

    # File handler (if log directory exists or can be created)
    log_path = Path(log_dir)
    try:
        log_path.mkdir(parents=True, exist_ok=True)

        if log_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = f"dockermonitor_{timestamp}.log"

        file_handler = logging.FileHandler(
            log_path / log_file, encoding="utf-8", mode="a"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)

        logger.debug(f"Logging to file: {log_path / log_file}")

    except (OSError, PermissionError) as e:
        logger.warning(f"Could not create log file: {e}. Logging to console only.")

    return logger


def get_logger(name: str = "dockermonitor") -> logging.Logger:
    """
    Get existing logger instance.

    Args:
        name: Logger name.

    Returns:
        Logger instance.
    """
    return logging.getLogger(name)


class LoggerAdapter:
    """
    Adapter to add context to log messages.

    Useful for adding host information to log messages.
    """

    def __init__(self, logger: logging.Logger, context: dict):
        """
        Initialize LoggerAdapter.

        Args:
            logger: Base logger instance.
            context: Context dictionary to add to messages.
        """
        self.logger = logger
        self.context = context

    def _format_message(self, msg: str) -> str:
        """Format message with context."""
        context_str = " | ".join(f"{k}={v}" for k, v in self.context.items())
        return f"[{context_str}] {msg}"

    def debug(self, msg: str, *args, **kwargs):
        """Log debug message with context."""
        self.logger.debug(self._format_message(msg), *args, **kwargs)

    def info(self, msg: str, *args, **kwargs):
        """Log info message with context."""
        self.logger.info(self._format_message(msg), *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        """Log warning message with context."""
        self.logger.warning(self._format_message(msg), *args, **kwargs)

    def error(self, msg: str, *args, **kwargs):
        """Log error message with context."""
        self.logger.error(self._format_message(msg), *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs):
        """Log critical message with context."""
        self.logger.critical(self._format_message(msg), *args, **kwargs)

    def exception(self, msg: str, *args, **kwargs):
        """Log exception with context."""
        self.logger.exception(self._format_message(msg), *args, **kwargs)
