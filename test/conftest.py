"""Shared test fixtures for assert-one-assert-per-pytest."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable


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
        )
        return result.returncode, result.stdout, result.stderr

    return runner


@pytest.fixture
def test_file(tmp_path: Path) -> Callable[[str], Path]:
    """Fixture for creating temporary test files.

    Returns:
        A function that creates a file with given content and returns its path.
    """

    def creator(content: str, filename: str = "test_example.py") -> Path:
        file_path = tmp_path / filename
        file_path.write_text(content)
        return file_path

    return creator
