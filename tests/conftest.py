"""
Pytest configuration and fixtures for DedSecOS tests.

This module provides shared fixtures and configuration for all tests.
"""

import os
import tempfile

# SET ENVIRONMENT VARIABLE BEFORE ANY IMPORTS
# This must happen at module level, before pytest collects tests,
# because test collection imports ui modules which import core.logging
_test_log_dir = os.path.join(tempfile.gettempdir(), "dedsec_test_logs")
os.environ["DEDSEC_LOG_DIR"] = _test_log_dir

import pytest


def pytest_configure(config):
    """
    Called before test collection begins.
    Ensures DEDSEC_LOG_DIR is set to a writable temp directory.
    """
    # Already set at module level, but ensure it's there
    if "DEDSEC_LOG_DIR" not in os.environ:
        os.environ["DEDSEC_LOG_DIR"] = _test_log_dir


@pytest.fixture(autouse=True)
def set_log_dir(tmp_path, monkeypatch):
    """
    Ensure each test uses an isolated temporary log directory.

    This prevents PermissionError when tests import modules that
    attempt to create log directories in CI environments.
    """
    log_dir = tmp_path / "logs"
    monkeypatch.setenv("DEDSEC_LOG_DIR", str(log_dir))


@pytest.fixture
def mock_canvas():
    """Provide a mock canvas for UI tests."""
    from unittest.mock import MagicMock

    canvas = MagicMock()
    canvas.winfo_width.return_value = 320
    canvas.winfo_height.return_value = 240
    return canvas
