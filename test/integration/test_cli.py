from __future__ import annotations

import importlib
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from test.samples import (
    ASYNC_TEST,
    BARE_CONTEXT_MANAGER,
    CLASS_METHOD,
    CLEAN,
    CONJUNCTION,
    CONJUNCTION_OF_THREE,
    CONJUNCTION_PLUS_ASSERT,
    DISJUNCTION,
    HELPER_AND_TEST,
    NESTED_CLASS,
    NESTED_FUNCTION,
    NON_PYTEST_WITH,
    NO_ASSERTS,
    NO_ASSERTS_TWICE,
    OTHER_MODULE_RAISES,
    OTHER_PYTEST_CONTEXT_MANAGER,
    PYTEST_RAISES,
    PYTEST_WARNS,
    RAISES_PLUS_ASSERT,
)
from unittest.mock import patch

import pytest

from assert_one_assert_per_pytest.scanner import iter_test_functions

RunCli = Callable[[list[str]], tuple[int, str, str]]
MakeFile = Callable[[str, str], Path]

ITER_SOURCE = "def test_a():\n    assert True\n\ndef helper():\n    pass\n"


@pytest.mark.integration
class TestCliExitCodes:
    def test_exit_0_no_findings(
        self, run_cli: RunCli, test_file: MakeFile
    ) -> None:
        path = test_file(CLEAN, "test_clean.py")
        assert run_cli([str(path)])[0] == 0

    def test_exit_1_with_findings(
        self, run_cli: RunCli, test_file: MakeFile
    ) -> None:
        path = test_file(NO_ASSERTS, "test_violation.py")
        assert run_cli([str(path)])[0] == 1

    def test_exit_2_missing_file(self, run_cli: RunCli) -> None:
        assert run_cli(["nonexistent.py"])[0] == 2

    def test_missing_file_is_reported(self, run_cli: RunCli) -> None:
        assert "not found" in run_cli(["nonexistent.py"])[2].lower()

    def test_warn_only_always_exit_0(
        self, run_cli: RunCli, test_file: MakeFile
    ) -> None:
        path = test_file(NO_ASSERTS, "test_violation.py")
        assert run_cli([str(path), "--warn-only"])[0] == 0


@pytest.mark.integration
class TestCliOutput:
    def test_default_output_is_one_line(self, default_output: str) -> None:
        assert len(default_output.split("\n")) == 1

    def test_default_output_has_four_fields(
        self, default_output_parts: list[str]
    ) -> None:
        assert len(default_output_parts) == 4

    def test_default_output_starts_with_path(
        self, default_output_parts: list[str]
    ) -> None:
        assert "test_example.py" in default_output_parts[0]

    def test_default_output_names_the_function(
        self, default_output_parts: list[str]
    ) -> None:
        assert default_output_parts[2] == "test_no_asserts"

    def test_default_output_reports_the_count(
        self, default_output_parts: list[str]
    ) -> None:
        assert default_output_parts[3] == "0"

    def test_count_output(self, run_cli: RunCli, test_file: MakeFile) -> None:
        path = test_file(NO_ASSERTS_TWICE, "test_example.py")
        assert run_cli([str(path), "--count"])[1].strip() == "2"

    def test_quiet_no_output(
        self, run_cli: RunCli, test_file: MakeFile
    ) -> None:
        path = test_file(NO_ASSERTS, "test_example.py")
        assert run_cli([str(path), "--quiet"])[1] == ""

    def test_quiet_still_exits_1(
        self, run_cli: RunCli, test_file: MakeFile
    ) -> None:
        path = test_file(NO_ASSERTS, "test_example.py")
        assert run_cli([str(path), "--quiet"])[0] == 1


@pytest.mark.integration
class TestCliFileDiscovery:
    def test_scans_directory_recursively(
        self, run_cli: RunCli, tmp_path: Path
    ) -> None:
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (tmp_path / "test_root.py").write_text("def test_root():\n    pass\n")
        (subdir / "test_nested.py").write_text("def test_nested():\n    pass\n")
        assert run_cli([str(tmp_path), "--count"])[1].strip() == "2"

    def test_exclude_patterns(self, run_cli: RunCli, tmp_path: Path) -> None:
        (tmp_path / "test_include.py").write_text("def test_i():\n    pass\n")
        (tmp_path / "test_exclude.py").write_text("def test_e():\n    pass\n")
        stdout = run_cli(
            [str(tmp_path), "--exclude", "**/test_exclude.py", "--count"]
        )[1]
        assert stdout.strip() == "1"

    def test_scans_non_test_named_files(
        self, run_cli: RunCli, tmp_path: Path
    ) -> None:
        (tmp_path / "test_valid.py").write_text("def test_valid():\n    pass\n")
        (tmp_path / "helper.py").write_text("def test_in_helper():\n    pass\n")
        assert run_cli([str(tmp_path), "--count"])[1].strip() == "2"

    def test_ignores_non_python_files_in_a_directory(
        self, run_cli: RunCli, tmp_path: Path
    ) -> None:
        (tmp_path / "test_valid.py").write_text("def test_valid():\n    pass\n")
        (tmp_path / "notes.txt").write_text("not python")
        assert run_cli([str(tmp_path), "--count"])[1].strip() == "1"

    def test_exclude_matches_filename(
        self, run_cli: RunCli, tmp_path: Path
    ) -> None:
        (tmp_path / "test_keep.py").write_text("def test_k():\n    pass\n")
        (tmp_path / "test_skip.py").write_text("def test_s():\n    pass\n")
        stdout = run_cli(
            [str(tmp_path), "--exclude", "test_skip.py", "--count"]
        )[1]
        assert stdout.strip() == "1"


@pytest.mark.integration
class TestCliFailFast:
    def test_stops_after_first_finding(
        self, run_cli: RunCli, tmp_path: Path
    ) -> None:
        (tmp_path / "test_a.py").write_text("def test_a():\n    pass\n")
        (tmp_path / "test_b.py").write_text("def test_b():\n    pass\n")
        assert run_cli([str(tmp_path), "--fail-fast"])[0] == 1

    def test_returns_exit_code_1(self, run_cli: RunCli, tmp_path: Path) -> None:
        (tmp_path / "test_single.py").write_text("def test_s():\n    pass\n")
        assert run_cli([str(tmp_path), "--fail-fast"])[0] == 1

    def test_reports_only_the_first_finding(
        self, run_cli: RunCli, tmp_path: Path
    ) -> None:
        (tmp_path / "test_single.py").write_text("def test_s():\n    pass\n")
        stdout = run_cli([str(tmp_path), "--fail-fast"])[1]
        assert len([ln for ln in stdout.strip().split("\n") if ln]) == 1


@pytest.mark.integration
class TestCliVerbose:
    def test_verbose_shows_scanning_info(
        self, run_cli: RunCli, test_file: MakeFile
    ) -> None:
        path = test_file("def test_x():\n    assert True\n", "test_v.py")
        assert "Scanning" in run_cli([str(path), "--verbose"])[1]

    def test_verbose_shows_files_scanned(
        self, run_cli: RunCli, test_file: MakeFile
    ) -> None:
        path = test_file("def test_x():\n    assert True\n", "test_v.py")
        assert "Files scanned:" in run_cli([str(path), "--verbose"])[1]

    def test_verbose_shows_exclude_patterns(
        self, run_cli: RunCli, tmp_path: Path
    ) -> None:
        (tmp_path / "test_x.py").write_text("def test_x():\n    assert True\n")
        stdout = run_cli(
            [str(tmp_path), "--verbose", "--exclude", "conftest.py"]
        )[1]
        assert "Excluding patterns:" in stdout

    def test_verbose_shows_findings(
        self, run_cli: RunCli, test_file: MakeFile
    ) -> None:
        path = test_file("def test_x():\n    pass\n", "test_v.py")
        assert "Found:" in run_cli([str(path), "--verbose"])[1]

    def test_verbose_shows_skipped_excluded(
        self, run_cli: RunCli, tmp_path: Path
    ) -> None:
        (tmp_path / "test_a.py").write_text("def test_a():\n    assert True\n")
        (tmp_path / "test_b.py").write_text("def test_b():\n    assert True\n")
        stdout = run_cli(
            [str(tmp_path), "--verbose", "--exclude", "test_b.py"]
        )[1]
        assert "Skipping (excluded):" in stdout

    def test_verbose_shows_errors(
        self, run_cli: RunCli, tmp_path: Path
    ) -> None:
        (tmp_path / "test_ok.py").write_text("def test_ok():\n    assert True\n")
        stdout = run_cli([str(tmp_path), "missing.py", "--verbose"])[1]
        assert "Errors occurred" in stdout

    def test_verbose_run_with_errors_exits_2(
        self, run_cli: RunCli, tmp_path: Path
    ) -> None:
        (tmp_path / "test_ok.py").write_text("def test_ok():\n    assert True\n")
        assert run_cli([str(tmp_path), "missing.py", "--verbose"])[0] == 2


@pytest.mark.integration
class TestCliErrorsAndGlobs:
    def test_syntax_error_exits_2(
        self, run_cli: RunCli, test_file: MakeFile
    ) -> None:
        path = test_file("def test_broken( invalid", "test_broken.py")
        assert run_cli([str(path)])[0] == 2

    def test_syntax_error_reports_error(
        self, run_cli: RunCli, test_file: MakeFile
    ) -> None:
        path = test_file("def test_broken( invalid", "test_broken.py")
        assert "syntax" in run_cli([str(path)])[2].lower()

    def test_glob_expands_to_directories(
        self, run_cli: RunCli, tmp_path: Path
    ) -> None:
        subdir = tmp_path / "tests"
        subdir.mkdir()
        (subdir / "test_a.py").write_text("def test_a():\n    pass\n")
        assert run_cli([f"{tmp_path}/*", "--count"])[1].strip() == "1"

    @pytest.mark.usefixtures("broken_symlink")
    def test_glob_ignores_broken_symlinks(
        self, run_cli: RunCli, tmp_path: Path
    ) -> None:
        (tmp_path / "test_real.py").write_text("def test_r():\n    pass\n")
        assert run_cli([f"{tmp_path}/test_*.py", "--count"])[1].strip() == "1"

    def test_deduplicates_files(
        self, run_cli: RunCli, test_file: MakeFile
    ) -> None:
        path = test_file("def test_x():\n    pass\n", "test_dup.py")
        assert run_cli([str(path), str(path), "--count"])[1].strip() == "1"


@pytest.mark.integration
class TestScannerIntegration:
    def test_ignores_nested_function_asserts(
        self, run_cli: RunCli, test_file: MakeFile
    ) -> None:
        path = test_file(NESTED_FUNCTION, "test_nested.py")
        assert run_cli([str(path)])[0] == 0

    def test_ignores_nested_class_asserts(
        self, run_cli: RunCli, test_file: MakeFile
    ) -> None:
        path = test_file(NESTED_CLASS, "test_nested_class.py")
        assert run_cli([str(path)])[0] == 0

    def test_detects_async_test_functions(
        self, run_cli: RunCli, test_file: MakeFile
    ) -> None:
        path = test_file(ASYNC_TEST, "test_async.py")
        assert run_cli([str(path)])[0] == 1

    def test_names_the_async_test_function(
        self, run_cli: RunCli, test_file: MakeFile
    ) -> None:
        path = test_file(ASYNC_TEST, "test_async.py")
        assert "test_async" in run_cli([str(path)])[1]

    def test_detects_class_test_methods(
        self, run_cli: RunCli, test_file: MakeFile
    ) -> None:
        path = test_file(CLASS_METHOD, "test_class.py")
        assert run_cli([str(path)])[0] == 1

    def test_names_the_class_test_method(
        self, run_cli: RunCli, test_file: MakeFile
    ) -> None:
        path = test_file(CLASS_METHOD, "test_class.py")
        assert "test_method" in run_cli([str(path)])[1]

    def test_ignores_non_test_functions(
        self, run_cli: RunCli, test_file: MakeFile
    ) -> None:
        path = test_file(HELPER_AND_TEST, "test_helper.py")
        assert run_cli([str(path)])[0] == 0

    def test_iter_test_functions_yields_one_result(self) -> None:
        assert len(list(iter_test_functions("test.py", ITER_SOURCE))) == 1

    def test_iter_test_functions_names_the_function(self) -> None:
        results = list(iter_test_functions("test.py", ITER_SOURCE))
        assert results[0][0] == "test_a"

    def test_pytest_raises_counts_as_assertion(
        self, run_cli: RunCli, test_file: MakeFile
    ) -> None:
        path = test_file(PYTEST_RAISES, "test_raises.py")
        assert run_cli([str(path)])[0] == 0

    def test_pytest_warns_counts_as_assertion(
        self, run_cli: RunCli, test_file: MakeFile
    ) -> None:
        path = test_file(PYTEST_WARNS, "test_warns.py")
        assert run_cli([str(path)])[0] == 0

    def test_pytest_raises_plus_assert_exits_1(
        self, run_cli: RunCli, test_file: MakeFile
    ) -> None:
        path = test_file(RAISES_PLUS_ASSERT, "test_two.py")
        assert run_cli([str(path)])[0] == 1

    def test_pytest_raises_plus_assert_counts_two(
        self, run_cli: RunCli, test_file: MakeFile
    ) -> None:
        path = test_file(RAISES_PLUS_ASSERT, "test_two.py")
        assert ":2" in run_cli([str(path)])[1]

    def test_non_pytest_context_manager_not_counted(
        self, run_cli: RunCli, test_file: MakeFile
    ) -> None:
        path = test_file(NON_PYTEST_WITH, "test_open.py")
        assert run_cli([str(path)])[0] == 0

    def test_context_manager_that_is_not_a_call_not_counted(
        self, run_cli: RunCli, test_file: MakeFile
    ) -> None:
        path = test_file(BARE_CONTEXT_MANAGER, "test_bare.py")
        assert run_cli([str(path)])[0] == 0

    def test_other_pytest_context_manager_not_counted(
        self, run_cli: RunCli, test_file: MakeFile
    ) -> None:
        path = test_file(OTHER_PYTEST_CONTEXT_MANAGER, "test_deprecated.py")
        assert run_cli([str(path)])[0] == 0

    def test_raises_on_another_module_not_counted(
        self, run_cli: RunCli, test_file: MakeFile
    ) -> None:
        path = test_file(OTHER_MODULE_RAISES, "test_other.py")
        assert run_cli([str(path)])[0] == 0


@pytest.mark.integration
class TestMainModuleAndEdgeCases:
    def test_main_module_runs(self, tmp_path: Path) -> None:
        path = tmp_path / "test_main.py"
        path.write_text("def test_x():\n    assert True\n")
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "assert_one_assert_per_pytest",
                str(path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0

    def test_main_module_import(self) -> None:
        sys.modules.pop("assert_one_assert_per_pytest.__main__", None)
        with patch("assert_one_assert_per_pytest.cli.main") as mock_main:
            importlib.import_module("assert_one_assert_per_pytest.__main__")
            assert mock_main.called

    def test_glob_matching_directory(
        self, run_cli: RunCli, tmp_path: Path
    ) -> None:
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "test_in_sub.py").write_text("def test_x():\n    pass\n")
        assert run_cli([f"{tmp_path}/sub*", "--count"])[1].strip() == "1"

    def test_duplicate_via_different_paths(
        self, run_cli: RunCli, tmp_path: Path
    ) -> None:
        path = tmp_path / "test_x.py"
        path.write_text("def test_x():\n    pass\n")
        other = str(tmp_path / "." / "test_x.py")
        assert run_cli([str(path), other, "--count"])[1].strip() == "1"

    def test_glob_no_matches_exits_2(
        self, run_cli: RunCli, tmp_path: Path
    ) -> None:
        assert run_cli([f"{tmp_path}/nonexistent_*.py"])[0] == 2

    def test_glob_no_matches_reports_not_found(
        self, run_cli: RunCli, tmp_path: Path
    ) -> None:
        stderr = run_cli([f"{tmp_path}/nonexistent_*.py"])[2]
        assert "not found" in stderr.lower()

    def test_glob_matching_file_directly(
        self, run_cli: RunCli, tmp_path: Path
    ) -> None:
        (tmp_path / "test_glob.py").write_text("def test_g():\n    pass\n")
        assert run_cli([f"{tmp_path}/test_*.py", "--count"])[1].strip() == "1"

    def test_skips_non_python_files(
        self, run_cli: RunCli, tmp_path: Path
    ) -> None:
        txt = tmp_path / "test_file.txt"
        txt.write_text("not python")
        real = tmp_path / "test_real.py"
        real.write_text("def test_r():\n    pass\n")
        stdout = run_cli([str(txt), str(real), "--count"])[1]
        assert stdout.strip() == "1"

    def test_scans_a_named_non_test_python_file(
        self, run_cli: RunCli, tmp_path: Path
    ) -> None:
        helper = tmp_path / "helper.py"
        helper.write_text("def test_in_helper():\n    pass\n")
        real = tmp_path / "test_real.py"
        real.write_text("def test_r():\n    pass\n")
        stdout = run_cli([str(helper), str(real), "--count"])[1]
        assert stdout.strip() == "2"

    def test_unreadable_file_exits_2(
        self, run_cli: RunCli, unreadable_file: Path
    ) -> None:
        assert run_cli([str(unreadable_file)])[0] == 2

    def test_unreadable_file_is_reported(
        self, run_cli: RunCli, unreadable_file: Path
    ) -> None:
        assert "error" in run_cli([str(unreadable_file)])[2].lower()


@pytest.mark.integration
class TestCliConjunctions:
    def test_exit_1_for_a_conjunction(
        self, run_cli: RunCli, test_file: MakeFile
    ) -> None:
        path = test_file(CONJUNCTION, "test_conjunction.py")
        assert run_cli([str(path)])[0] == 1

    def test_exit_0_for_a_disjunction(
        self, run_cli: RunCli, test_file: MakeFile
    ) -> None:
        path = test_file(DISJUNCTION, "test_disjunction.py")
        assert run_cli([str(path)])[0] == 0

    def test_output_marks_the_conjunction(
        self, run_cli: RunCli, test_file: MakeFile
    ) -> None:
        path = test_file(CONJUNCTION, "test_conjunction.py")
        assert run_cli([str(path)])[1].strip().endswith(":conjunction")

    def test_output_names_the_number_of_conjuncts(
        self, run_cli: RunCli, test_file: MakeFile
    ) -> None:
        path = test_file(CONJUNCTION_OF_THREE, "test_conjunction.py")
        assert ":3:conjunction" in run_cli([str(path)])[1]

    def test_count_mode_counts_both_kinds(
        self, run_cli: RunCli, test_file: MakeFile
    ) -> None:
        path = test_file(CONJUNCTION_PLUS_ASSERT, "test_both.py")
        assert run_cli([str(path), "--count"])[1].strip() == "2"

    def test_verbose_reports_the_conjunction(
        self, run_cli: RunCli, test_file: MakeFile
    ) -> None:
        path = test_file(CONJUNCTION, "test_conjunction.py")
        assert "conjunction" in run_cli([str(path), "--verbose"])[1]
