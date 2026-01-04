"""Root pytest configuration and shared test utilities."""

from __future__ import annotations

import io
import subprocess
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import TYPE_CHECKING
import pytest

from assert_one_assert_per_pytest.cli import main

if TYPE_CHECKING:
    from collections.abc import Callable


def pytest_configure(config: pytest.Config) -> None:
    """Register custom pytest markers."""
    config.addinivalue_line("markers", "unit: unit tests")
    config.addinivalue_line("markers", "integration: integration tests")
    config.addinivalue_line("markers", "e2e: end-to-end tests")


@pytest.fixture
def run_cli() -> Callable[[list[str]], tuple[int, str, str]]:
    """Fixture providing in-process CLI runner for coverage tracking.

    Returns:
        A function that runs the CLI with given arguments and returns
        (exit_code, stdout, stderr).
    """

    def runner(args: list[str]) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        exit_code = 0

        with redirect_stdout(stdout), redirect_stderr(stderr):
            try:
                main(args)
            except SystemExit as e:
                exit_code = int(e.code) if e.code is not None else 0

        return exit_code, stdout.getvalue(), stderr.getvalue()

    return runner


@pytest.fixture
def run_cli_subprocess() -> Callable[[list[str]], tuple[int, str, str]]:
    """Fixture providing subprocess-based CLI runner for e2e tests.

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
