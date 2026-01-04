"""Integration tests for the CLI with real files."""

from __future__ import annotations

import importlib
import os
import stat
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from assert_one_assert_per_pytest.scanner import iter_test_functions

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

    def test_exclude_matches_filename(
        self,
        run_cli: Callable[[list[str]], tuple[int, str, str]],
        tmp_path: Path,
    ) -> None:
        """Exclude patterns match by filename."""
        (tmp_path / "test_keep.py").write_text("def test_k():\n    pass\n")
        (tmp_path / "test_skip.py").write_text("def test_s():\n    pass\n")
        _, stdout, _ = run_cli([str(tmp_path), "--exclude", "test_skip.py", "--count"])
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

        exit_code, _, _ = run_cli([str(tmp_path), "--fail-fast"])
        assert exit_code == 1

    def test_returns_exit_code_1(
        self,
        run_cli: Callable[[list[str]], tuple[int, str, str]],
        tmp_path: Path,
    ) -> None:
        """--fail-fast returns exit code 1 on finding."""
        (tmp_path / "test_single.py").write_text(
            """
def test_single():
    pass
"""
        )

        exit_code, stdout, _ = run_cli([str(tmp_path), "--fail-fast"])
        assert exit_code == 1
        lines = [line for line in stdout.strip().split("\n") if line]
        assert len(lines) == 1


@pytest.mark.integration
class TestCliVerbose:
    """Tests for --verbose output."""

    def test_verbose_shows_scanning_info(
        self,
        run_cli: Callable[[list[str]], tuple[int, str, str]],
        test_file: Callable[[str, str], Path],
    ) -> None:
        """--verbose shows scanning progress."""
        path = test_file("def test_x():\n    assert True\n", "test_v.py")
        _, stdout, _ = run_cli([str(path), "--verbose"])
        assert "Scanning" in stdout
        assert "Files scanned:" in stdout

    def test_verbose_shows_exclude_patterns(
        self,
        run_cli: Callable[[list[str]], tuple[int, str, str]],
        tmp_path: Path,
    ) -> None:
        """--verbose shows exclude patterns."""
        (tmp_path / "test_x.py").write_text("def test_x():\n    assert True\n")
        _, stdout, _ = run_cli(
            [str(tmp_path), "--verbose", "--exclude", "conftest.py"]
        )
        assert "Excluding patterns:" in stdout

    def test_verbose_shows_findings(
        self,
        run_cli: Callable[[list[str]], tuple[int, str, str]],
        test_file: Callable[[str, str], Path],
    ) -> None:
        """--verbose shows individual findings."""
        path = test_file("def test_x():\n    pass\n", "test_v.py")
        _, stdout, _ = run_cli([str(path), "--verbose"])
        assert "Found:" in stdout

    def test_verbose_shows_skipped_excluded(
        self,
        run_cli: Callable[[list[str]], tuple[int, str, str]],
        tmp_path: Path,
    ) -> None:
        """--verbose shows skipped excluded files."""
        (tmp_path / "test_a.py").write_text("def test_a():\n    assert True\n")
        (tmp_path / "test_b.py").write_text("def test_b():\n    assert True\n")
        _, stdout, _ = run_cli(
            [str(tmp_path), "--verbose", "--exclude", "test_b.py"]
        )
        assert "Skipping (excluded):" in stdout

    def test_verbose_shows_errors(
        self,
        run_cli: Callable[[list[str]], tuple[int, str, str]],
        tmp_path: Path,
    ) -> None:
        """--verbose shows errors occurred message."""
        (tmp_path / "test_ok.py").write_text("def test_ok():\n    assert True\n")
        exit_code, stdout, _ = run_cli([str(tmp_path), "missing.py", "--verbose"])
        assert "Errors occurred" in stdout
        assert exit_code == 2


@pytest.mark.integration
class TestCliErrorsAndGlobs:
    """Tests for error handling and glob patterns."""

    def test_syntax_error_reports_error(
        self,
        run_cli: Callable[[list[str]], tuple[int, str, str]],
        test_file: Callable[[str, str], Path],
    ) -> None:
        """Syntax errors are reported."""
        path = test_file("def test_broken( invalid", "test_broken.py")
        exit_code, _, stderr = run_cli([str(path)])
        assert exit_code == 2
        assert "syntax" in stderr.lower()

    def test_glob_expands_to_directories(
        self,
        run_cli: Callable[[list[str]], tuple[int, str, str]],
        tmp_path: Path,
    ) -> None:
        """Glob patterns expand to include directories."""
        subdir = tmp_path / "tests"
        subdir.mkdir()
        (subdir / "test_a.py").write_text("def test_a():\n    pass\n")
        _, stdout, _ = run_cli([f"{tmp_path}/*", "--count"])
        assert stdout.strip() == "1"

    def test_deduplicates_files(
        self,
        run_cli: Callable[[list[str]], tuple[int, str, str]],
        test_file: Callable[[str, str], Path],
    ) -> None:
        """Duplicate file references are deduplicated."""
        path = test_file("def test_x():\n    pass\n", "test_dup.py")
        _, stdout, _ = run_cli([str(path), str(path), "--count"])
        assert stdout.strip() == "1"


@pytest.mark.integration
class TestScannerIntegration:
    """Tests for scanner integration."""

    def test_ignores_nested_function_asserts(
        self,
        run_cli: Callable[[list[str]], tuple[int, str, str]],
        test_file: Callable[[str, str], Path],
    ) -> None:
        """Asserts in nested functions are not counted."""
        path = test_file(
            """
def test_with_nested():
    def helper():
        assert False
    assert True
""",
            "test_nested.py",
        )
        exit_code, _, _ = run_cli([str(path)])
        assert exit_code == 0

    def test_ignores_nested_class_asserts(
        self,
        run_cli: Callable[[list[str]], tuple[int, str, str]],
        test_file: Callable[[str, str], Path],
    ) -> None:
        """Asserts in nested classes are not counted."""
        path = test_file(
            """
def test_with_nested_class():
    class Helper:
        def check(self):
            assert False
    assert True
""",
            "test_nested_class.py",
        )
        exit_code, _, _ = run_cli([str(path)])
        assert exit_code == 0

    def test_detects_async_test_functions(
        self,
        run_cli: Callable[[list[str]], tuple[int, str, str]],
        test_file: Callable[[str, str], Path],
    ) -> None:
        """Async test functions are detected."""
        path = test_file("async def test_async():\n    pass\n", "test_async.py")
        exit_code, stdout, _ = run_cli([str(path)])
        assert exit_code == 1
        assert "test_async" in stdout

    def test_detects_class_test_methods(
        self,
        run_cli: Callable[[list[str]], tuple[int, str, str]],
        test_file: Callable[[str, str], Path],
    ) -> None:
        """Test methods in classes are detected."""
        path = test_file(
            """
class TestClass:
    def test_method(self):
        pass
""",
            "test_class.py",
        )
        exit_code, stdout, _ = run_cli([str(path)])
        assert exit_code == 1
        assert "test_method" in stdout

    def test_ignores_non_test_functions(
        self,
        run_cli: Callable[[list[str]], tuple[int, str, str]],
        test_file: Callable[[str, str], Path],
    ) -> None:
        """Non-test functions are ignored."""
        path = test_file(
            """
def helper():
    pass

def test_only():
    assert True
""",
            "test_helper.py",
        )
        exit_code, _, _ = run_cli([str(path)])
        assert exit_code == 0

    def test_iter_test_functions_integration(self) -> None:
        """Test iter_test_functions yields correct data."""
        code = "def test_a():\n    assert True\n\ndef helper():\n    pass\n"
        results = list(iter_test_functions("test.py", code))
        assert len(results) == 1
        assert results[0][0] == "test_a"

    def test_pytest_raises_counts_as_assertion(
        self,
        run_cli: Callable[[list[str]], tuple[int, str, str]],
        test_file: Callable[[str, str], Path],
    ) -> None:
        """pytest.raises() context manager counts as an assertion."""
        path = test_file(
            """
import pytest

def test_raises_exception():
    with pytest.raises(ValueError):
        raise ValueError("expected")
""",
            "test_raises.py",
        )
        exit_code, _, _ = run_cli([str(path)])
        assert exit_code == 0

    def test_pytest_warns_counts_as_assertion(
        self,
        run_cli: Callable[[list[str]], tuple[int, str, str]],
        test_file: Callable[[str, str], Path],
    ) -> None:
        """pytest.warns() context manager counts as an assertion."""
        path = test_file(
            """
import pytest

def test_warns_user():
    with pytest.warns(UserWarning):
        import warnings
        warnings.warn("expected", UserWarning)
""",
            "test_warns.py",
        )
        exit_code, _, _ = run_cli([str(path)])
        assert exit_code == 0

    def test_pytest_raises_plus_assert_is_two_assertions(
        self,
        run_cli: Callable[[list[str]], tuple[int, str, str]],
        test_file: Callable[[str, str], Path],
    ) -> None:
        """pytest.raises() plus assert statement counts as two assertions."""
        path = test_file(
            """
import pytest

def test_two_assertions():
    with pytest.raises(ValueError):
        raise ValueError("expected")
    assert True
""",
            "test_two.py",
        )
        exit_code, stdout, _ = run_cli([str(path)])
        assert exit_code == 1
        assert "test_two_assertions" in stdout
        assert ":2" in stdout

    def test_non_pytest_context_manager_not_counted(
        self,
        run_cli: Callable[[list[str]], tuple[int, str, str]],
        test_file: Callable[[str, str], Path],
    ) -> None:
        """Non-pytest context managers don't count as assertions."""
        path = test_file(
            """
def test_with_open():
    with open(__file__) as f:
        pass
    assert True
""",
            "test_open.py",
        )
        exit_code, _, _ = run_cli([str(path)])
        assert exit_code == 0


@pytest.mark.integration
class TestMainModuleAndEdgeCases:
    """Tests for __main__ module and edge cases."""

    def test_main_module_runs(self, tmp_path: Path) -> None:
        """Test running as python -m module."""
        test_file = tmp_path / "test_main.py"
        test_file.write_text("def test_x():\n    assert True\n")
        result = subprocess.run(
            [sys.executable, "-m", "assert_one_assert_per_pytest", str(test_file)],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0

    def test_main_module_import(self) -> None:
        """Test that __main__ module can be imported and calls main."""
        sys.modules.pop("assert_one_assert_per_pytest.__main__", None)
        with patch("assert_one_assert_per_pytest.cli.main") as mock_main:
            importlib.import_module("assert_one_assert_per_pytest.__main__")
            assert mock_main.called

    def test_glob_matching_directory(
        self,
        run_cli: Callable[[list[str]], tuple[int, str, str]],
        tmp_path: Path,
    ) -> None:
        """Glob matches directory and expands it."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "test_in_sub.py").write_text("def test_x():\n    pass\n")
        _, stdout, _ = run_cli([f"{tmp_path}/sub*", "--count"])
        assert stdout.strip() == "1"

    def test_duplicate_via_different_paths(
        self,
        run_cli: Callable[[list[str]], tuple[int, str, str]],
        tmp_path: Path,
    ) -> None:
        """Duplicates via different path forms are deduplicated."""
        test_file = tmp_path / "test_x.py"
        test_file.write_text("def test_x():\n    pass\n")
        path1 = str(test_file)
        path2 = str(tmp_path / "." / "test_x.py")
        _, stdout, _ = run_cli([path1, path2, "--count"])
        assert stdout.strip() == "1"

    def test_glob_no_matches(
        self,
        run_cli: Callable[[list[str]], tuple[int, str, str]],
        tmp_path: Path,
    ) -> None:
        """Glob pattern with no matches reports error."""
        exit_code, _, stderr = run_cli([f"{tmp_path}/nonexistent_*.py"])
        assert exit_code == 2
        assert "not found" in stderr.lower()

    def test_glob_matching_file_directly(
        self,
        run_cli: Callable[[list[str]], tuple[int, str, str]],
        tmp_path: Path,
    ) -> None:
        """Glob matching a file directly works."""
        test_file = tmp_path / "test_glob.py"
        test_file.write_text("def test_g():\n    pass\n")
        _, stdout, _ = run_cli([f"{tmp_path}/test_*.py", "--count"])
        assert stdout.strip() == "1"

    def test_skips_non_python_files(
        self,
        run_cli: Callable[[list[str]], tuple[int, str, str]],
        tmp_path: Path,
    ) -> None:
        """Non-.py files passed directly are skipped."""
        txt_file = tmp_path / "test_file.txt"
        txt_file.write_text("not python")
        test_file = tmp_path / "test_real.py"
        test_file.write_text("def test_r():\n    pass\n")
        _, stdout, _ = run_cli([str(txt_file), str(test_file), "--count"])
        assert stdout.strip() == "1"

    def test_skips_non_test_python_files(
        self,
        run_cli: Callable[[list[str]], tuple[int, str, str]],
        tmp_path: Path,
    ) -> None:
        """Non-test .py files passed directly are skipped."""
        helper = tmp_path / "helper.py"
        helper.write_text("def helper():\n    pass\n")
        test_file = tmp_path / "test_real.py"
        test_file.write_text("def test_r():\n    pass\n")
        _, stdout, _ = run_cli([str(helper), str(test_file), "--count"])
        assert stdout.strip() == "1"

    def test_unreadable_file(
        self,
        run_cli: Callable[[list[str]], tuple[int, str, str]],
        tmp_path: Path,
    ) -> None:
        """Unreadable files are reported as errors."""
        test_file = tmp_path / "test_unreadable.py"
        test_file.write_text("def test_u():\n    pass\n")
        os.chmod(test_file, 0o000)
        try:
            exit_code, _, stderr = run_cli([str(test_file)])
            assert exit_code == 2
            assert "error" in stderr.lower()
        finally:
            os.chmod(test_file, stat.S_IRUSR | stat.S_IWUSR)
