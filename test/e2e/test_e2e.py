from __future__ import annotations

from pathlib import Path
from test.helpers import run_tool
from test.samples import (
    ASYNC_TEST,
    CLASS_METHOD,
    HELPER_AND_TEST,
    NESTED_FUNCTION,
    NO_ASSERTS,
    NO_ASSERTS_TWICE,
    PYTEST_RAISES,
    PYTEST_WARNS,
    RAISES_PLUS_ASSERT,
    THREE_ASSERTS,
    TWO_CLEAN,
)

import pytest


@pytest.mark.e2e
class TestCliExitCodes:
    def test_exit_0_when_all_tests_have_one_assert(
        self, tmp_path: Path
    ) -> None:
        path = tmp_path / "test_clean.py"
        path.write_text(TWO_CLEAN)
        assert run_tool(str(path)).returncode == 0

    def test_exit_1_when_test_has_no_asserts(self, tmp_path: Path) -> None:
        path = tmp_path / "test_violation.py"
        path.write_text(NO_ASSERTS)
        assert run_tool(str(path)).returncode == 1

    def test_exit_1_when_test_has_multiple_asserts(
        self, tmp_path: Path
    ) -> None:
        path = tmp_path / "test_violation.py"
        path.write_text(THREE_ASSERTS)
        assert run_tool(str(path)).returncode == 1

    def test_exit_2_when_file_not_found(self) -> None:
        assert run_tool("nonexistent_file.py").returncode == 2

    def test_missing_file_is_reported(self) -> None:
        assert "not found" in run_tool("nonexistent_file.py").stderr.lower()

    def test_exit_2_when_syntax_error(self, tmp_path: Path) -> None:
        path = tmp_path / "test_broken.py"
        path.write_text("def test_broken( invalid syntax")
        assert run_tool(str(path)).returncode == 2


@pytest.mark.e2e
class TestOutputFormat:
    def test_default_output_has_three_separators(
        self, default_output: str
    ) -> None:
        assert default_output.count(":") == 3

    def test_default_output_names_the_file(self, default_output: str) -> None:
        assert "test_output.py" in default_output

    def test_default_output_names_the_function(
        self, default_output: str
    ) -> None:
        assert "test_empty" in default_output

    def test_default_output_ends_with_the_count(
        self, default_output: str
    ) -> None:
        assert default_output.endswith(":0")

    def test_count_mode_outputs_only_count(self, tmp_path: Path) -> None:
        path = tmp_path / "test_example.py"
        path.write_text(NO_ASSERTS_TWICE)
        assert run_tool(str(path), "--count").stdout.strip() == "2"

    def test_quiet_mode_produces_no_output(self, tmp_path: Path) -> None:
        path = tmp_path / "test_example.py"
        path.write_text(NO_ASSERTS)
        assert run_tool(str(path), "--quiet").stdout == ""

    def test_quiet_mode_still_exits_1(self, tmp_path: Path) -> None:
        path = tmp_path / "test_example.py"
        path.write_text(NO_ASSERTS)
        assert run_tool(str(path), "--quiet").returncode == 1

    def test_verbose_mode_shows_scanning(self, verbose_output: str) -> None:
        assert "Scanning" in verbose_output

    def test_verbose_mode_shows_files_scanned(
        self, verbose_output: str
    ) -> None:
        assert "Files scanned:" in verbose_output

    def test_verbose_mode_shows_findings(self, verbose_output: str) -> None:
        assert "Findings:" in verbose_output


@pytest.mark.e2e
class TestFileDiscovery:
    def test_scans_directory_recursively(self, tmp_path: Path) -> None:
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (tmp_path / "test_root.py").write_text("\ndef test_root():\n    pass\n")
        (subdir / "test_nested.py").write_text(
            "\ndef test_nested():\n    pass\n"
        )
        assert run_tool(str(tmp_path), "--count").stdout.strip() == "2"

    def test_only_scans_test_files(self, tmp_path: Path) -> None:
        (tmp_path / "test_valid.py").write_text(
            "\ndef test_valid():\n    pass\n"
        )
        (tmp_path / "helper.py").write_text(
            "\ndef test_in_helper():\n    pass\n"
        )
        (tmp_path / "conftest.py").write_text(
            "\ndef test_in_conftest():\n    pass\n"
        )
        assert run_tool(str(tmp_path), "--count").stdout.strip() == "1"

    def test_exclude_patterns(self, tmp_path: Path) -> None:
        (tmp_path / "test_include.py").write_text(
            "\ndef test_included():\n    pass\n"
        )
        (tmp_path / "test_exclude.py").write_text(
            "\ndef test_excluded():\n    pass\n"
        )
        result = run_tool(
            str(tmp_path), "--exclude", "**/test_exclude.py", "--count"
        )
        assert result.stdout.strip() == "1"

    def test_glob_patterns(self, tmp_path: Path) -> None:
        subdir = tmp_path / "tests"
        subdir.mkdir()
        (subdir / "test_a.py").write_text("\ndef test_a():\n    pass\n")
        (subdir / "test_b.py").write_text("\ndef test_b():\n    pass\n")
        result = run_tool(f"{tmp_path}/tests/test_*.py", "--count")
        assert result.stdout.strip() == "2"

    def test_skips_hidden_directories(self, tmp_path: Path) -> None:
        hidden_dir = tmp_path / ".hidden"
        hidden_dir.mkdir()
        (tmp_path / "test_visible.py").write_text(
            "\ndef test_visible():\n    pass\n"
        )
        (hidden_dir / "test_hidden.py").write_text(
            "\ndef test_hidden():\n    pass\n"
        )
        assert run_tool(str(tmp_path), "--count").stdout.strip() == "1"


@pytest.mark.e2e
class TestBehaviorFlags:
    def test_fail_fast_reports_one_finding(self, tmp_path: Path) -> None:
        (tmp_path / "test_a.py").write_text("\ndef test_a():\n    pass\n")
        (tmp_path / "test_b.py").write_text("\ndef test_b():\n    pass\n")
        stdout = run_tool(str(tmp_path), "--fail-fast").stdout
        assert len([ln for ln in stdout.strip().split("\n") if ln]) == 1

    def test_fail_fast_exits_1(self, tmp_path: Path) -> None:
        (tmp_path / "test_a.py").write_text("\ndef test_a():\n    pass\n")
        (tmp_path / "test_b.py").write_text("\ndef test_b():\n    pass\n")
        assert run_tool(str(tmp_path), "--fail-fast").returncode == 1

    def test_warn_only_always_exits_0(self, tmp_path: Path) -> None:
        path = tmp_path / "test_violation.py"
        path.write_text(NO_ASSERTS)
        assert run_tool(str(path), "--warn-only").returncode == 0


@pytest.mark.e2e
class TestTestFunctionTypes:
    def test_detects_async_test_functions(self, tmp_path: Path) -> None:
        path = tmp_path / "test_async.py"
        path.write_text(ASYNC_TEST)
        assert run_tool(str(path)).returncode == 1

    def test_names_the_async_test_function(self, tmp_path: Path) -> None:
        path = tmp_path / "test_async.py"
        path.write_text(ASYNC_TEST)
        assert "test_async" in run_tool(str(path)).stdout

    def test_detects_class_test_methods(self, tmp_path: Path) -> None:
        path = tmp_path / "test_class.py"
        path.write_text(CLASS_METHOD)
        assert run_tool(str(path)).returncode == 1

    def test_names_the_class_test_method(self, tmp_path: Path) -> None:
        path = tmp_path / "test_class.py"
        path.write_text(CLASS_METHOD)
        assert "test_method" in run_tool(str(path)).stdout

    def test_ignores_nested_function_asserts(self, tmp_path: Path) -> None:
        path = tmp_path / "test_nested.py"
        path.write_text(NESTED_FUNCTION)
        assert run_tool(str(path)).returncode == 0

    def test_ignores_non_test_functions(self, tmp_path: Path) -> None:
        path = tmp_path / "test_example.py"
        path.write_text(HELPER_AND_TEST)
        assert run_tool(str(path)).returncode == 0

    def test_pytest_raises_counts_as_assertion(self, tmp_path: Path) -> None:
        path = tmp_path / "test_raises.py"
        path.write_text(PYTEST_RAISES)
        assert run_tool(str(path)).returncode == 0

    def test_pytest_warns_counts_as_assertion(self, tmp_path: Path) -> None:
        path = tmp_path / "test_warns.py"
        path.write_text(PYTEST_WARNS)
        assert run_tool(str(path)).returncode == 0

    def test_pytest_raises_plus_assert_exits_1(self, tmp_path: Path) -> None:
        path = tmp_path / "test_two.py"
        path.write_text(RAISES_PLUS_ASSERT)
        assert run_tool(str(path)).returncode == 1

    def test_pytest_raises_plus_assert_names_the_function(
        self, tmp_path: Path
    ) -> None:
        path = tmp_path / "test_two.py"
        path.write_text(RAISES_PLUS_ASSERT)
        assert "test_two_assertions" in run_tool(str(path)).stdout

    def test_pytest_raises_plus_assert_counts_two(
        self, tmp_path: Path
    ) -> None:
        path = tmp_path / "test_two.py"
        path.write_text(RAISES_PLUS_ASSERT)
        assert ":2" in run_tool(str(path)).stdout


@pytest.mark.e2e
class TestEdgeCases:
    def test_empty_test_file(self, tmp_path: Path) -> None:
        path = tmp_path / "test_empty.py"
        path.write_text("")
        assert run_tool(str(path)).returncode == 0

    def test_multiple_files_with_mixed_results(self, tmp_path: Path) -> None:
        (tmp_path / "test_clean.py").write_text(
            "\ndef test_clean():\n    assert True\n"
        )
        (tmp_path / "test_zero.py").write_text(
            "\ndef test_zero():\n    pass\n"
        )
        (tmp_path / "test_many.py").write_text(
            "\ndef test_many():\n    assert True\n    assert False\n"
        )
        assert run_tool(str(tmp_path), "--count").stdout.strip() == "2"

    def test_reports_correct_line_numbers(self, tmp_path: Path) -> None:
        path = tmp_path / "test_lines.py"
        path.write_text("x = 1\ny = 2\ndef test_on_line_3():\n    pass\n")
        assert ":3:" in run_tool(str(path)).stdout

    def test_deduplicates_files(self, tmp_path: Path) -> None:
        path = tmp_path / "test_dupe.py"
        path.write_text("\ndef test_example():\n    pass\n")
        result = run_tool(str(path), str(path), "--count")
        assert result.stdout.strip() == "1"
