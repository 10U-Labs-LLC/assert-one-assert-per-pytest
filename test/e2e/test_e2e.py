"""End-to-end tests for assert-one-assert-per-pytest CLI."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    """Run the CLI as a subprocess."""
    return subprocess.run(
        [sys.executable, "-m", "assert_one_assert_per_pytest", *args],
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.mark.e2e
class TestCliExitCodes:
    """Tests for CLI exit codes."""

    def test_exit_0_when_all_tests_have_one_assert(self, tmp_path: Path) -> None:
        """Exit code 0 when all tests have exactly one assert."""
        test_file = tmp_path / "test_clean.py"
        test_file.write_text(
            """
def test_example():
    assert True

def test_another():
    assert 1 == 1
"""
        )
        result = run_cli(str(test_file))
        assert result.returncode == 0

    def test_exit_1_when_test_has_no_asserts(self, tmp_path: Path) -> None:
        """Exit code 1 when a test has no asserts."""
        test_file = tmp_path / "test_violation.py"
        test_file.write_text(
            """
def test_no_asserts():
    pass
"""
        )
        result = run_cli(str(test_file))
        assert result.returncode == 1

    def test_exit_1_when_test_has_multiple_asserts(self, tmp_path: Path) -> None:
        """Exit code 1 when a test has multiple asserts."""
        test_file = tmp_path / "test_violation.py"
        test_file.write_text(
            """
def test_many_asserts():
    assert True
    assert False
    assert 1 == 1
"""
        )
        result = run_cli(str(test_file))
        assert result.returncode == 1

    def test_exit_2_when_file_not_found(self) -> None:
        """Exit code 2 when file doesn't exist."""
        result = run_cli("nonexistent_file.py")
        assert result.returncode == 2
        assert "not found" in result.stderr.lower()

    def test_exit_2_when_syntax_error(self, tmp_path: Path) -> None:
        """Exit code 2 when file has syntax error."""
        test_file = tmp_path / "test_broken.py"
        test_file.write_text("def test_broken( invalid syntax")
        result = run_cli(str(test_file))
        assert result.returncode == 2


@pytest.mark.e2e
class TestOutputFormat:
    """Tests for output format."""

    def test_default_output_shows_path_line_function_count(
        self, tmp_path: Path
    ) -> None:
        """Default output format is path:line:function:count."""
        test_file = tmp_path / "test_output.py"
        test_file.write_text(
            """
def test_empty():
    pass
"""
        )
        result = run_cli(str(test_file))
        output = result.stdout.strip()
        assert output.count(":") == 3
        assert "test_output.py" in output
        assert "test_empty" in output
        assert output.endswith(":0")

    def test_count_mode_outputs_only_count(self, tmp_path: Path) -> None:
        """--count outputs only the number of findings."""
        test_file = tmp_path / "test_example.py"
        test_file.write_text(
            """
def test_no_asserts():
    pass

def test_also_no_asserts():
    x = 1
"""
        )
        result = run_cli(str(test_file), "--count")
        assert result.stdout.strip() == "2"

    def test_quiet_mode_produces_no_output(self, tmp_path: Path) -> None:
        """--quiet produces no stdout output."""
        test_file = tmp_path / "test_example.py"
        test_file.write_text(
            """
def test_no_asserts():
    pass
"""
        )
        result = run_cli(str(test_file), "--quiet")
        assert result.stdout == ""
        assert result.returncode == 1

    def test_verbose_mode_shows_details(self, tmp_path: Path) -> None:
        """--verbose shows scanning progress and summary."""
        test_file = tmp_path / "test_example.py"
        test_file.write_text(
            """
def test_one_assert():
    assert True
"""
        )
        result = run_cli(str(test_file), "--verbose")
        assert "Scanning" in result.stdout
        assert "Files scanned:" in result.stdout
        assert "Findings:" in result.stdout


@pytest.mark.e2e
class TestFileDiscovery:
    """Tests for file discovery and filtering."""

    def test_scans_directory_recursively(self, tmp_path: Path) -> None:
        """Directories are scanned recursively for test files."""
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

        result = run_cli(str(tmp_path), "--count")
        assert result.stdout.strip() == "2"

    def test_only_scans_test_files(self, tmp_path: Path) -> None:
        """Only test_*.py and *_test.py files are scanned."""
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
        (tmp_path / "conftest.py").write_text(
            """
def test_in_conftest():
    pass
"""
        )

        result = run_cli(str(tmp_path), "--count")
        assert result.stdout.strip() == "1"

    def test_exclude_patterns(self, tmp_path: Path) -> None:
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

        result = run_cli(str(tmp_path), "--exclude", "**/test_exclude.py", "--count")
        assert result.stdout.strip() == "1"

    def test_glob_patterns(self, tmp_path: Path) -> None:
        """Glob patterns are supported for file selection."""
        subdir = tmp_path / "tests"
        subdir.mkdir()

        (subdir / "test_a.py").write_text(
            """
def test_a():
    pass
"""
        )
        (subdir / "test_b.py").write_text(
            """
def test_b():
    pass
"""
        )

        result = run_cli(f"{tmp_path}/tests/test_*.py", "--count")
        assert result.stdout.strip() == "2"

    def test_skips_hidden_directories(self, tmp_path: Path) -> None:
        """Hidden directories (.hidden) are skipped."""
        hidden_dir = tmp_path / ".hidden"
        hidden_dir.mkdir()

        (tmp_path / "test_visible.py").write_text(
            """
def test_visible():
    pass
"""
        )
        (hidden_dir / "test_hidden.py").write_text(
            """
def test_hidden():
    pass
"""
        )

        result = run_cli(str(tmp_path), "--count")
        assert result.stdout.strip() == "1"


@pytest.mark.e2e
class TestBehaviorFlags:
    """Tests for behavior modification flags."""

    def test_fail_fast_stops_after_first_finding(self, tmp_path: Path) -> None:
        """--fail-fast stops after first finding."""
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

        result = run_cli(str(tmp_path), "--fail-fast")
        lines = [line for line in result.stdout.strip().split("\n") if line]
        assert len(lines) == 1
        assert result.returncode == 1

    def test_warn_only_always_exits_0(self, tmp_path: Path) -> None:
        """--warn-only always exits with code 0."""
        test_file = tmp_path / "test_violation.py"
        test_file.write_text(
            """
def test_no_asserts():
    pass
"""
        )
        result = run_cli(str(test_file), "--warn-only")
        assert result.returncode == 0


@pytest.mark.e2e
class TestTestFunctionTypes:
    """Tests for different test function types."""

    def test_detects_async_test_functions(self, tmp_path: Path) -> None:
        """Async test functions are detected."""
        test_file = tmp_path / "test_async.py"
        test_file.write_text(
            """
async def test_async():
    pass
"""
        )
        result = run_cli(str(test_file))
        assert result.returncode == 1
        assert "test_async" in result.stdout

    def test_detects_class_test_methods(self, tmp_path: Path) -> None:
        """Test methods in classes are detected."""
        test_file = tmp_path / "test_class.py"
        test_file.write_text(
            """
class TestExample:
    def test_method(self):
        pass
"""
        )
        result = run_cli(str(test_file))
        assert result.returncode == 1
        assert "test_method" in result.stdout

    def test_ignores_nested_function_asserts(self, tmp_path: Path) -> None:
        """Asserts in nested functions are not counted."""
        test_file = tmp_path / "test_nested.py"
        test_file.write_text(
            """
def test_with_helper():
    def helper():
        assert False  # This should not be counted
    assert True  # Only this one counts
"""
        )
        result = run_cli(str(test_file))
        assert result.returncode == 0

    def test_ignores_non_test_functions(self, tmp_path: Path) -> None:
        """Non-test functions are ignored."""
        test_file = tmp_path / "test_example.py"
        test_file.write_text(
            """
def helper_function():
    pass  # No assert, but not a test

def test_example():
    assert True
"""
        )
        result = run_cli(str(test_file))
        assert result.returncode == 0


@pytest.mark.e2e
class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_test_file(self, tmp_path: Path) -> None:
        """Empty test files are handled gracefully."""
        test_file = tmp_path / "test_empty.py"
        test_file.write_text("")
        result = run_cli(str(test_file))
        assert result.returncode == 0

    def test_multiple_files_with_mixed_results(self, tmp_path: Path) -> None:
        """Multiple files with different results are all reported."""
        (tmp_path / "test_clean.py").write_text(
            """
def test_clean():
    assert True
"""
        )
        (tmp_path / "test_zero.py").write_text(
            """
def test_zero():
    pass
"""
        )
        (tmp_path / "test_many.py").write_text(
            """
def test_many():
    assert True
    assert False
"""
        )

        result = run_cli(str(tmp_path), "--count")
        assert result.stdout.strip() == "2"

    def test_reports_correct_line_numbers(self, tmp_path: Path) -> None:
        """Line numbers are reported correctly."""
        test_file = tmp_path / "test_lines.py"
        test_file.write_text(
            """# Line 1
# Line 2
def test_on_line_3():
    pass
"""
        )
        result = run_cli(str(test_file))
        assert ":3:" in result.stdout

    def test_deduplicates_files(self, tmp_path: Path) -> None:
        """Duplicate file references are deduplicated."""
        test_file = tmp_path / "test_dupe.py"
        test_file.write_text(
            """
def test_example():
    pass
"""
        )
        result = run_cli(str(test_file), str(test_file), "--count")
        assert result.stdout.strip() == "1"
