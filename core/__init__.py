"""DedSecOS Core Package - Security tools and business logic.

Modules:
    logging: Structured logging with multiple handlers and performance tracking

Example:
    from core.logging import get_logger, log_performance, audit_log

    logger = get_logger(__name__)
    logger.info("Application started")
"""

from core.logging import (
    PerformanceMonitor,
    audit_log,
    error_boundary,
    get_logger,
    log_error,
    log_performance,
    performance_monitor,
    setup_logging,
)

__version__ = "3.2.0"

__all__ = [
    "setup_logging",
    "get_logger",
    "log_error",
    "audit_log",
    "log_performance",
    "error_boundary",
    "PerformanceMonitor",
    "performance_monitor",
]
