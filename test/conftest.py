"""Root pytest configuration and shared test utilities."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from assert_one_assert_per_pytest.cli import main

if TYPE_CHECKING:
    from collections.abc import Callable


def pytest_configure(config: pytest.Config) -> None:
    """Register custom pytest markers."""
    config.addinivalue_line("markers", "unit: unit tests")
    config.addinivalue_line("markers", "integration: integration tests")
    config.addinivalue_line("markers", "e2e: end-to-end tests")


def run_main_with_args(args: list[str]) -> int:
    """Run main() with given args and return exit code.

    Shared utility for CLI tests across unit, integration, and e2e test suites.
    """
    with patch("sys.argv", ["assert-one-assert-per-pytest", *args]):
        try:
            main()
            return 0
        except SystemExit as e:
            return int(e.code) if e.code is not None else 0


@pytest.fixture
def run_cli() -> Callable[[list[str]], tuple[int, str, str]]:
    """Fixture providing subprocess-based CLI runner.

    Returns:
        A function that runs the CLI with given arguments and returns
        (exit_code, stdout, stderr).
    """

    def runner(args: list[str]) -> tuple[int, str, str]:
        result = subprocess.run(
            [sys.executable, "-m", "assert_one_assert_per_pytest", *args],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode, result.stdout, result.stderr

    return runner


@pytest.fixture
def test_file(tmp_path: Path) -> Callable[[str, str], Path]:
    """Fixture for creating temporary test files.

    Returns:
        A function that creates a file with given content and returns its path.
    """

    def creator(content: str, filename: str = "test_example.py") -> Path:
        file_path = tmp_path / filename
        file_path.write_text(content)
        return file_path

    return creator
