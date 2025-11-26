"""
Pytest configuration and fixtures for DedSecOS tests.

This module provides shared fixtures and configuration for all tests.
"""

import os
import pytest


@pytest.fixture(autouse=True)
def set_log_dir(tmp_path, monkeypatch):
    """
    Ensure tests use a temporary writable log directory.

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
