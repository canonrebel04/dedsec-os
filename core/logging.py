"""
DedSecOS Logging Framework

Provides structured logging with multiple handlers, error boundaries, and
performance monitoring for the DedSec cyberdeck application.

This module establishes a comprehensive logging system that:
- Configures root logger with file rotation
- Provides console output with color coding
- Creates audit trail for security events
- Tracks performance metrics
- Implements error boundaries with context
- Integrates with DEBUG flags from config

Architecture:
    Root Logger
    ├── FileHandler (rotating, /home/cachy/dedsec/logs/dedsec.log)
    ├── ConsoleHandler (color-coded output)
    ├── AuditHandler (security events, /home/cachy/dedsec/logs/audit.log)
    └── PerformanceHandler (metrics, /home/cachy/dedsec/logs/performance.log)

Log Levels:
    DEBUG: Detailed diagnostic information
    INFO: General informational messages
    WARNING: Warning messages (recoverable errors)
    ERROR: Error messages (failures)
    CRITICAL: Critical errors (system failure)

Usage:
    from core.logging import get_logger, log_error, log_performance, audit_log

    # Get module logger
    logger = get_logger(__name__)
    logger.info("Module initialized")

    # Log errors with context
    log_error("Failed to load config", exc_info=True, context={"file": "config.py"})

    # Track performance
    with log_performance("wifi_scan"):
        scan_wifi()

    # Audit security events
    audit_log("WIFI_DEAUTH", target="AA:BB:CC:DD:EE:FF", success=True)
"""

import logging
import logging.handlers
import os
import sys
import time
import traceback
import functools
from typing import Optional, Dict, Any, Callable
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager

# Import config for paths and debug flags
try:
    from config import DEBUG  # type: ignore[attr-defined]

    DEBUG_MODE = DEBUG.ENABLE_DEBUG_LOGGING if hasattr(DEBUG, "ENABLE_DEBUG_LOGGING") else False
except ImportError:
    DEBUG_MODE = False

# Constants - Use relative path from project root or temp directory
# Detect project root (where this file's parent's parent is)
_PROJECT_ROOT = Path(__file__).parent.parent
LOG_DIR = _PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIR / "dedsec.log"
AUDIT_LOG_FILE = LOG_DIR / "audit.log"
PERFORMANCE_LOG_FILE = LOG_DIR / "performance.log"
ERROR_LOG_FILE = LOG_DIR / "errors.log"

MAX_LOG_SIZE = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5  # Keep 5 backup files


# ANSI color codes for console output
class LogColors:
    """ANSI color codes for terminal output."""

    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    DIM = "\033[2m"


class ColoredFormatter(logging.Formatter):
    """Custom formatter with color-coded output for console."""

    LEVEL_COLORS = {
        logging.DEBUG: LogColors.CYAN,
        logging.INFO: LogColors.GREEN,
        logging.WARNING: LogColors.YELLOW,
        logging.ERROR: LogColors.RED,
        logging.CRITICAL: LogColors.RED + LogColors.BOLD,
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        # Color the level name
        levelname = record.levelname
        if record.levelno in self.LEVEL_COLORS:
            levelname = f"{self.LEVEL_COLORS[record.levelno]}{levelname}{LogColors.RESET}"

        # Store original levelname
        original_levelname = record.levelname
        record.levelname = levelname

        # Format the message
        result = super().format(record)

        # Restore original levelname
        record.levelname = original_levelname

        return result


class AuditFormatter(logging.Formatter):
    """Custom formatter for audit log entries."""

    def format(self, record: logging.LogRecord) -> str:
        """Format audit log with timestamp, event type, and details."""
        timestamp = datetime.fromtimestamp(record.created).isoformat()

        # Extract audit fields from record
        event_type = getattr(record, "event_type", "UNKNOWN")
        user = getattr(record, "user", os.getlogin())
        details = getattr(record, "details", {})
        success = getattr(record, "success", True)

        # Format details as key=value pairs
        details_str = " ".join(f"{k}={v}" for k, v in details.items())
        status = "SUCCESS" if success else "FAILURE"

        return f"{timestamp} | {event_type} | {user} | {status} | {details_str}"


class PerformanceFormatter(logging.Formatter):
    """Custom formatter for performance metrics."""

    def format(self, record: logging.LogRecord) -> str:
        """Format performance log with timing information."""
        timestamp = datetime.fromtimestamp(record.created).isoformat()

        # Extract performance fields
        operation = getattr(record, "operation", "UNKNOWN")
        duration_ms = getattr(record, "duration_ms", 0)
        details = getattr(record, "details", {})

        # Format details
        details_str = " ".join(f"{k}={v}" for k, v in details.items())

        return f"{timestamp} | {operation} | {duration_ms:.2f}ms | {details_str}"


def setup_logging(
    log_level: int = logging.INFO,
    enable_console: bool = True,
    enable_file: bool = True,
    enable_audit: bool = True,
    enable_performance: bool = True,
) -> None:
    """
    Configure the root logger with multiple handlers.

    Sets up file rotation, console output, audit logging, and performance
    tracking. Creates log directory if it doesn't exist.

    Args:
        log_level: Minimum log level (logging.DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_console: Enable colored console output
        enable_file: Enable file logging with rotation
        enable_audit: Enable security audit logging
        enable_performance: Enable performance metrics logging

    Example:
        setup_logging(log_level=logging.DEBUG, enable_console=True)
    """
    # Create log directory if it doesn't exist
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
    except (PermissionError, OSError):
        # Fall back to temp directory if we can't write to project root
        import tempfile

        global LOG_DIR, LOG_FILE, AUDIT_LOG_FILE, PERFORMANCE_LOG_FILE, ERROR_LOG_FILE
        LOG_DIR = Path(tempfile.gettempdir()) / "dedsec_logs"
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        LOG_FILE = LOG_DIR / "dedsec.log"
        AUDIT_LOG_FILE = LOG_DIR / "audit.log"
        PERFORMANCE_LOG_FILE = LOG_DIR / "performance.log"
        ERROR_LOG_FILE = LOG_DIR / "errors.log"

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level if DEBUG_MODE else logging.INFO)

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # File handler with rotation
    if enable_file:
        file_handler = logging.handlers.RotatingFileHandler(
            LOG_FILE, maxBytes=MAX_LOG_SIZE, backupCount=BACKUP_COUNT, encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s | %(name)s | %(levelname)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    # Console handler with colors
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = ColoredFormatter("%(levelname)s | %(name)s | %(message)s")
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    # Audit log handler (separate file for security events)
    if enable_audit:
        audit_handler = logging.handlers.RotatingFileHandler(
            AUDIT_LOG_FILE, maxBytes=MAX_LOG_SIZE, backupCount=BACKUP_COUNT, encoding="utf-8"
        )
        audit_handler.setLevel(logging.INFO)
        audit_handler.setFormatter(AuditFormatter())

        # Create separate audit logger
        audit_logger = logging.getLogger("audit")
        audit_logger.addHandler(audit_handler)
        audit_logger.propagate = False  # Don't propagate to root logger

    # Performance log handler
    if enable_performance:
        perf_handler = logging.handlers.RotatingFileHandler(
            PERFORMANCE_LOG_FILE, maxBytes=MAX_LOG_SIZE, backupCount=BACKUP_COUNT, encoding="utf-8"
        )
        perf_handler.setLevel(logging.DEBUG)
        perf_handler.setFormatter(PerformanceFormatter())

        # Create separate performance logger
        perf_logger = logging.getLogger("performance")
        perf_logger.addHandler(perf_handler)
        perf_logger.propagate = False

    # Error log handler (separate file for errors only)
    error_handler = logging.handlers.RotatingFileHandler(
        ERROR_LOG_FILE, maxBytes=MAX_LOG_SIZE, backupCount=BACKUP_COUNT, encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_formatter = logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)s | %(pathname)s:%(lineno)d | %(message)s\n%(exc_info)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    error_handler.setFormatter(error_formatter)
    root_logger.addHandler(error_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.

    Args:
        name: Module name (usually __name__)

    Returns:
        Configured logger instance

    Example:
        logger = get_logger(__name__)
        logger.info("Module initialized")
    """
    return logging.getLogger(name)


def log_error(
    message: str,
    exc_info: bool = False,
    context: Optional[Dict[str, Any]] = None,
    logger_name: Optional[str] = None,
) -> None:
    """
    Log an error with optional context and exception information.

    Args:
        message: Error message
        exc_info: Include exception traceback
        context: Additional context dictionary
        logger_name: Logger name (defaults to 'error')

    Example:
        log_error("Failed to load config",
                 exc_info=True,
                 context={"file": "config.py", "line": 42})
    """
    logger = get_logger(logger_name or "error")

    # Build full message with context
    if context:
        context_str = " | ".join(f"{k}={v}" for k, v in context.items())
        full_message = f"{message} | {context_str}"
    else:
        full_message = message

    logger.error(full_message, exc_info=exc_info)


def audit_log(
    event_type: str, success: bool = True, user: Optional[str] = None, **details: Any
) -> None:
    """
    Log a security audit event.

    Creates an audit trail of security-relevant events like authentication,
    authorization, data access, configuration changes, etc.

    Args:
        event_type: Type of event (e.g., "LOGIN", "WIFI_SCAN", "DEAUTH_ATTACK")
        success: Whether the event succeeded
        user: Username (defaults to current user)
        **details: Additional event details as keyword arguments

    Example:
        audit_log("WIFI_DEAUTH",
                 success=True,
                 target="AA:BB:CC:DD:EE:FF",
                 packets=5)
    """
    logger = logging.getLogger("audit")

    # Create log record with custom fields
    record = logger.makeRecord(logger.name, logging.INFO, "", 0, "", (), None)
    record.event_type = event_type
    record.success = success
    record.user = user or os.getlogin()
    record.details = details

    logger.handle(record)


@contextmanager
def log_performance(operation: str, logger_name: Optional[str] = None, **details: Any):
    """
    Context manager for performance tracking.

    Measures execution time of a code block and logs to performance log.

    Args:
        operation: Name of the operation being measured
        logger_name: Logger name (defaults to 'performance')
        **details: Additional details to log

    Example:
        with log_performance("wifi_scan", network_count=12):
            scan_wifi()

    Yields:
        None
    """
    logger = logging.getLogger(logger_name or "performance")
    start_time = time.perf_counter()

    try:
        yield
    finally:
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Create log record with custom fields
        record = logger.makeRecord(logger.name, logging.DEBUG, "", 0, "", (), None)
        record.operation = operation
        record.duration_ms = duration_ms
        record.details = details

        logger.handle(record)


def error_boundary(
    fallback_value: Any = None, log_traceback: bool = True, reraise: bool = False
) -> Callable:
    """
    Decorator that creates an error boundary around a function.

    Catches exceptions, logs them, and optionally returns a fallback value
    or re-raises the exception.

    Args:
        fallback_value: Value to return if exception occurs
        log_traceback: Include full traceback in log
        reraise: Re-raise exception after logging

    Returns:
        Decorated function

    Example:
        @error_boundary(fallback_value=[], log_traceback=True)
        def get_networks():
            return scan_wifi()
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                log_error(
                    f"Exception in {func.__name__}: {str(e)}",
                    exc_info=log_traceback,
                    context={
                        "function": func.__name__,
                        "args": str(args)[:100],  # Limit length
                        "kwargs": str(kwargs)[:100],
                    },
                )

                if reraise:
                    raise

                return fallback_value

        return wrapper

    return decorator


class PerformanceMonitor:
    """
    Performance monitoring utility for tracking operation metrics.

    Tracks min/max/average execution times for operations and provides
    statistics for performance analysis.

    Example:
        monitor = PerformanceMonitor()

        with monitor.measure("wifi_scan"):
            scan_wifi()

        stats = monitor.get_stats("wifi_scan")
        print(f"Average: {stats['avg_ms']:.2f}ms")
    """

    def __init__(self):
        """Initialize performance monitor."""
        self.measurements: Dict[str, list] = {}
        self.logger = get_logger("performance_monitor")

    @contextmanager
    def measure(self, operation: str, **details: Any):
        """
        Measure execution time of a code block.

        Args:
            operation: Name of the operation
            **details: Additional details to log

        Yields:
            None
        """
        start_time = time.perf_counter()

        try:
            yield
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Store measurement
            if operation not in self.measurements:
                self.measurements[operation] = []
            self.measurements[operation].append(duration_ms)

            # Log to performance log
            with log_performance(operation, **details):
                pass

    def get_stats(self, operation: str) -> Dict[str, float]:
        """
        Get statistics for an operation.

        Args:
            operation: Name of the operation

        Returns:
            Dictionary with min, max, avg, count statistics

        Example:
            stats = monitor.get_stats("wifi_scan")
            # {'min_ms': 120.5, 'max_ms': 543.2, 'avg_ms': 234.7, 'count': 10}
        """
        if operation not in self.measurements:
            return {"min_ms": 0, "max_ms": 0, "avg_ms": 0, "count": 0}

        measurements = self.measurements[operation]

        return {
            "min_ms": min(measurements),
            "max_ms": max(measurements),
            "avg_ms": sum(measurements) / len(measurements),
            "count": len(measurements),
        }

    def reset(self, operation: Optional[str] = None) -> None:
        """
        Reset measurements for an operation or all operations.

        Args:
            operation: Operation name (if None, resets all)
        """
        if operation:
            self.measurements.pop(operation, None)
        else:
            self.measurements.clear()


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


# Initialize logging on module import
setup_logging()
