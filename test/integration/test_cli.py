"""Integration tests for the CLI with real files."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable


@pytest.mark.integration
class TestCliExitCodes:
    """Tests for CLI exit codes."""

    def test_exit_0_no_findings(
        self,
        run_cli: Callable[[list[str]], tuple[int, str, str]],
        test_file: Callable[[str, str], Path],
    ) -> None:
        """Exit code 0 when all tests have exactly one assert."""
        path = test_file(
            """
def test_example():
    assert True
""",
            "test_clean.py",
        )
        exit_code, _, _ = run_cli([str(path)])
        assert exit_code == 0

    def test_exit_1_with_findings(
        self,
        run_cli: Callable[[list[str]], tuple[int, str, str]],
        test_file: Callable[[str, str], Path],
    ) -> None:
        """Exit code 1 when findings exist."""
        path = test_file(
            """
def test_no_asserts():
    pass
""",
            "test_violation.py",
        )
        exit_code, _, _ = run_cli([str(path)])
        assert exit_code == 1

    def test_exit_2_missing_file(
        self,
        run_cli: Callable[[list[str]], tuple[int, str, str]],
    ) -> None:
        """Exit code 2 when file doesn't exist."""
        exit_code, _, stderr = run_cli(["nonexistent.py"])
        assert exit_code == 2
        assert "not found" in stderr.lower()

    def test_warn_only_always_exit_0(
        self,
        run_cli: Callable[[list[str]], tuple[int, str, str]],
        test_file: Callable[[str, str], Path],
    ) -> None:
        """--warn-only always exits with 0."""
        path = test_file(
            """
def test_no_asserts():
    pass
""",
            "test_violation.py",
        )
        exit_code, _, _ = run_cli([str(path), "--warn-only"])
        assert exit_code == 0


@pytest.mark.integration
class TestCliOutput:
    """Tests for CLI output formats."""

    def test_default_output_format(
        self,
        run_cli: Callable[[list[str]], tuple[int, str, str]],
        test_file: Callable[[str, str], Path],
    ) -> None:
        """Default output shows path:line:name:count."""
        path = test_file(
            """
def test_no_asserts():
    pass
""",
            "test_example.py",
        )
        _, stdout, _ = run_cli([str(path)])
        lines = stdout.strip().split("\n")
        assert len(lines) == 1
        parts = lines[0].split(":")
        assert len(parts) == 4
        assert "test_example.py" in parts[0]
        assert parts[2] == "test_no_asserts"
        assert parts[3] == "0"

    def test_count_output(
        self,
        run_cli: Callable[[list[str]], tuple[int, str, str]],
        test_file: Callable[[str, str], Path],
    ) -> None:
        """--count outputs only the count."""
        path = test_file(
            """
def test_no_asserts():
    pass

def test_also_no_asserts():
    x = 1
""",
            "test_example.py",
        )
        _, stdout, _ = run_cli([str(path), "--count"])
        assert stdout.strip() == "2"

    def test_quiet_no_output(
        self,
        run_cli: Callable[[list[str]], tuple[int, str, str]],
        test_file: Callable[[str, str], Path],
    ) -> None:
        """--quiet produces no stdout output."""
        path = test_file(
            """
def test_no_asserts():
    pass
""",
            "test_example.py",
        )
        exit_code, stdout, _ = run_cli([str(path), "--quiet"])
        assert stdout == ""
        assert exit_code == 1


@pytest.mark.integration
class TestCliFileDiscovery:
    """Tests for file discovery and filtering."""

    def test_scans_directory_recursively(
        self,
        run_cli: Callable[[list[str]], tuple[int, str, str]],
        tmp_path: Path,
    ) -> None:
        """Scans directories recursively for test files."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        (tmp_path / "test_root.py").write_text(
            """
def test_root():
    pass
"""
        )
        (subdir / "test_nested.py").write_text(
            """
def test_nested():
    pass
"""
        )

        _, stdout, _ = run_cli([str(tmp_path), "--count"])
        assert stdout.strip() == "2"

    def test_exclude_patterns(
        self,
        run_cli: Callable[[list[str]], tuple[int, str, str]],
        tmp_path: Path,
    ) -> None:
        """--exclude filters out matching files."""
        (tmp_path / "test_include.py").write_text(
            """
def test_included():
    pass
"""
        )
        (tmp_path / "test_exclude.py").write_text(
            """
def test_excluded():
    pass
"""
        )

        _, stdout, _ = run_cli(
            [str(tmp_path), "--exclude", "**/test_exclude.py", "--count"]
        )
        assert stdout.strip() == "1"

    def test_ignores_non_test_files(
        self,
        run_cli: Callable[[list[str]], tuple[int, str, str]],
        tmp_path: Path,
    ) -> None:
        """Only scans test_*.py and *_test.py files."""
        (tmp_path / "test_valid.py").write_text(
            """
def test_valid():
    pass
"""
        )
        (tmp_path / "helper.py").write_text(
            """
def test_in_helper():
    pass
"""
        )

        _, stdout, _ = run_cli([str(tmp_path), "--count"])
        assert stdout.strip() == "1"


@pytest.mark.integration
class TestCliFailFast:
    """Tests for --fail-fast behavior."""

    def test_stops_after_first_finding(
        self,
        run_cli: Callable[[list[str]], tuple[int, str, str]],
        tmp_path: Path,
    ) -> None:
        """--fail-fast stops after first finding."""
        # Create multiple files with violations
        (tmp_path / "test_a.py").write_text(
            """
def test_a():
    pass
"""
        )
        (tmp_path / "test_b.py").write_text(
            """
def test_b():
    pass
"""
        )

        exit_code, stdout, _ = run_cli([str(tmp_path), "--fail-fast"])
        assert exit_code == 1
        # Should only show one finding
        lines = [line for line in stdout.strip().split("\n") if line]
        assert len(lines) == 1
