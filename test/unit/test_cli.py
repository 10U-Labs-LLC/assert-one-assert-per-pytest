from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from assert_one_assert_per_pytest.cli import (
    ScanResult,
    _expand_directory,
    _expand_glob,
    _is_glob_pattern,
    _iter_files,
    _should_skip_file,
    create_parser,
    determine_exit_code,
    output_findings,
    parse_patterns,
    process_files,
)
from assert_one_assert_per_pytest.scanner import Finding

RunCli = Callable[[list[str]], tuple[int, str, str]]
MakeFile = Callable[[str, str], Path]


@pytest.mark.unit
class TestCreateParser:
    def test_requires_files_argument(self) -> None:
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_accepts_single_file(self) -> None:
        args = create_parser().parse_args(["test_example.py"])
        assert args.files == ["test_example.py"]

    def test_accepts_multiple_files(self) -> None:
        args = create_parser().parse_args(["test_a.py", "test_b.py"])
        assert args.files == ["test_a.py", "test_b.py"]

    def test_accepts_exclude_option(self) -> None:
        args = create_parser().parse_args(
            ["tests/", "--exclude", "**/conftest.py"]
        )
        assert args.exclude == "**/conftest.py"

    def test_quiet_flag(self) -> None:
        args = create_parser().parse_args(["tests/", "--quiet"])
        assert args.quiet is True

    def test_count_flag(self) -> None:
        args = create_parser().parse_args(["tests/", "--count"])
        assert args.count is True

    def test_verbose_flag(self) -> None:
        args = create_parser().parse_args(["tests/", "--verbose"])
        assert args.verbose is True

    def test_fail_fast_flag(self) -> None:
        args = create_parser().parse_args(["tests/", "--fail-fast"])
        assert args.fail_fast is True

    def test_warn_only_flag(self) -> None:
        args = create_parser().parse_args(["tests/", "--warn-only"])
        assert args.warn_only is True

    def test_output_modes_mutually_exclusive(self) -> None:
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["tests/", "--quiet", "--count"])

    def test_behavior_modes_mutually_exclusive(self) -> None:
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["tests/", "--fail-fast", "--warn-only"])


@pytest.mark.unit
class TestParsePatterns:
    def test_returns_empty_for_none(self) -> None:
        assert parse_patterns(None) == []

    def test_returns_empty_for_empty_string(self) -> None:
        assert parse_patterns("") == []

    def test_parses_single_pattern(self) -> None:
        assert parse_patterns("*.py") == ["*.py"]

    def test_parses_multiple_patterns(self) -> None:
        assert parse_patterns("*.py,*.txt,*.md") == ["*.py", "*.txt", "*.md"]

    def test_strips_whitespace(self) -> None:
        assert parse_patterns(" *.py , *.txt ") == ["*.py", "*.txt"]

    def test_ignores_empty_entries(self) -> None:
        assert parse_patterns("*.py,,*.txt,") == ["*.py", "*.txt"]


@pytest.mark.unit
class TestIsGlobPattern:
    def test_detects_asterisk(self) -> None:
        assert _is_glob_pattern("*.py") is True

    def test_detects_question_mark(self) -> None:
        assert _is_glob_pattern("test?.py") is True

    def test_detects_bracket(self) -> None:
        assert _is_glob_pattern("test[0-9].py") is True

    def test_regular_path_is_not_glob(self) -> None:
        assert _is_glob_pattern("test/example.py") is False


@pytest.mark.unit
class TestExpandDirectory:
    def test_finds_test_files(self, tmp_path: Path) -> None:
        (tmp_path / "test_example.py").write_text("")
        assert len(_expand_directory(str(tmp_path))) == 1

    def test_finds_test_suffix_files(self, tmp_path: Path) -> None:
        (tmp_path / "example_test.py").write_text("")
        assert len(_expand_directory(str(tmp_path))) == 1

    def test_ignores_non_test_files(self, tmp_path: Path) -> None:
        (tmp_path / "helper.py").write_text("")
        assert len(_expand_directory(str(tmp_path))) == 0

    def test_ignores_non_python_files(self, tmp_path: Path) -> None:
        (tmp_path / "notes.txt").write_text("")
        assert len(_expand_directory(str(tmp_path))) == 0

    def test_recurses_into_subdirectories(self, tmp_path: Path) -> None:
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "test_nested.py").write_text("")
        assert len(_expand_directory(str(tmp_path))) == 1

    def test_skips_hidden_directories(self, tmp_path: Path) -> None:
        hidden = tmp_path / ".hidden"
        hidden.mkdir()
        (hidden / "test_hidden.py").write_text("")
        assert len(_expand_directory(str(tmp_path))) == 0


@pytest.mark.unit
class TestExpandGlob:
    def test_returns_matching_files(self, tmp_path: Path) -> None:
        (tmp_path / "test_a.py").write_text("")
        (tmp_path / "test_b.py").write_text("")
        files, _ = _expand_glob(f"{tmp_path}/test_*.py")
        assert len(files) == 2

    def test_reports_a_match_was_found(self, tmp_path: Path) -> None:
        (tmp_path / "test_a.py").write_text("")
        _, found = _expand_glob(f"{tmp_path}/test_*.py")
        assert found is True

    def test_returns_no_files_for_no_matches(self) -> None:
        files, _ = _expand_glob("/nonexistent/path/*.py")
        assert not files

    def test_reports_no_match_was_found(self) -> None:
        _, found = _expand_glob("/nonexistent/path/*.py")
        assert found is False

    def test_expands_directories_in_glob(self, tmp_path: Path) -> None:
        subdir = tmp_path / "tests"
        subdir.mkdir()
        (subdir / "test_example.py").write_text("")
        files, _ = _expand_glob(str(subdir))
        assert len(files) == 1

    def test_reports_a_match_for_a_directory(self, tmp_path: Path) -> None:
        subdir = tmp_path / "tests"
        subdir.mkdir()
        (subdir / "test_example.py").write_text("")
        _, found = _expand_glob(str(subdir))
        assert found is True

    @pytest.mark.usefixtures("broken_symlink")
    def test_ignores_matches_that_are_neither_file_nor_directory(
        self, tmp_path: Path
    ) -> None:
        files, _ = _expand_glob(f"{tmp_path}/test_*.py")
        assert not files

    @pytest.mark.usefixtures("broken_symlink")
    def test_reports_a_match_for_a_broken_symlink(
        self, tmp_path: Path
    ) -> None:
        _, found = _expand_glob(f"{tmp_path}/test_*.py")
        assert found is True


@pytest.mark.unit
class TestIterFiles:
    def test_handles_single_file(self, tmp_path: Path) -> None:
        path = tmp_path / "test_example.py"
        path.write_text("")
        files, _ = _iter_files([str(path)])
        assert len(files) == 1

    def test_reports_no_missing_for_existing_file(self, tmp_path: Path) -> None:
        path = tmp_path / "test_example.py"
        path.write_text("")
        _, missing = _iter_files([str(path)])
        assert not missing

    def test_handles_directory(self, tmp_path: Path) -> None:
        (tmp_path / "test_example.py").write_text("")
        files, _ = _iter_files([str(tmp_path)])
        assert len(files) == 1

    def test_handles_glob_pattern(self, tmp_path: Path) -> None:
        (tmp_path / "test_a.py").write_text("")
        (tmp_path / "test_b.py").write_text("")
        files, _ = _iter_files([f"{tmp_path}/test_*.py"])
        assert len(files) == 2

    def test_returns_no_files_for_missing_path(self) -> None:
        files, _ = _iter_files(["/nonexistent/path.py"])
        assert not files

    def test_reports_missing_paths(self) -> None:
        _, missing = _iter_files(["/nonexistent/path.py"])
        assert len(missing) == 1

    def test_returns_no_files_for_missing_glob(self) -> None:
        files, _ = _iter_files(["/nonexistent/*.py"])
        assert not files

    def test_reports_missing_glob(self) -> None:
        _, missing = _iter_files(["/nonexistent/*.py"])
        assert len(missing) == 1

    def test_deduplicates_files(self, tmp_path: Path) -> None:
        path = tmp_path / "test_example.py"
        path.write_text("")
        files, _ = _iter_files([str(path), str(path)])
        assert len(files) == 1


@pytest.mark.unit
class TestShouldSkipFile:
    def test_no_patterns_returns_false(self) -> None:
        assert _should_skip_file("test.py", []) is False

    def test_matches_full_path(self) -> None:
        assert _should_skip_file("path/to/test.py", ["path/to/test.py"]) is True

    def test_matches_filename(self) -> None:
        assert _should_skip_file("path/to/conftest.py", ["conftest.py"]) is True

    def test_matches_glob_pattern(self) -> None:
        assert (
            _should_skip_file("path/to/test_skip.py", ["**/test_skip.py"])
            is True
        )

    def test_no_match_returns_false(self) -> None:
        assert _should_skip_file("test.py", ["other.py"]) is False


@pytest.mark.unit
class TestProcessFiles:
    def test_counts_the_scanned_file(self, test_file: MakeFile) -> None:
        path = test_file("def test_a():\n    pass\n", "test_example.py")
        assert process_files([str(path)], []).files_scanned == 1

    def test_reports_the_finding(self, test_file: MakeFile) -> None:
        path = test_file("def test_a():\n    pass\n", "test_example.py")
        assert len(process_files([str(path)], []).findings) == 1

    def test_skips_non_python_files(self, test_file: MakeFile) -> None:
        path = test_file("content", "readme.txt")
        assert process_files([str(path)], []).files_scanned == 0

    def test_skips_non_test_files(self, test_file: MakeFile) -> None:
        path = test_file("def helper():\n    pass\n", "helper.py")
        assert process_files([str(path)], []).files_scanned == 0

    def test_respects_exclude_patterns(self, test_file: MakeFile) -> None:
        path = test_file("def test_a():\n    pass\n", "test_skip.py")
        result = process_files([str(path)], ["**/test_skip.py"])
        assert result.files_scanned == 0

    def test_handles_syntax_errors(self, test_file: MakeFile) -> None:
        path = test_file("def test_a( broken", "test_broken.py")
        assert process_files([str(path)], []).had_error is True

    def test_fail_fast_stops_early(self, tmp_path: Path) -> None:
        (tmp_path / "test_a.py").write_text("def test_a():\n    pass\n")
        (tmp_path / "test_b.py").write_text("def test_b():\n    pass\n")
        result = process_files(
            [str(tmp_path / "test_a.py"), str(tmp_path / "test_b.py")],
            [],
            fail_fast=True,
        )
        assert len(result.findings) == 1

    def test_verbose_output(
        self,
        test_file: MakeFile,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        path = test_file("def test_a():\n    assert True\n", "test_verbose.py")
        process_files([str(path)], [], verbose=True)
        assert "Scanning:" in capsys.readouterr().out

    def test_verbose_shows_excluded(
        self,
        test_file: MakeFile,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        path = test_file("def test_a():\n    pass\n", "test_skip.py")
        process_files([str(path)], ["**/test_skip.py"], verbose=True)
        assert "Skipping (excluded):" in capsys.readouterr().out

    def test_verbose_shows_findings(
        self,
        test_file: MakeFile,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        path = test_file("def test_a():\n    pass\n", "test_findings.py")
        process_files([str(path)], [], verbose=True)
        assert "Found:" in capsys.readouterr().out

    def test_read_error_sets_had_error(self, unreadable_file: Path) -> None:
        assert process_files([str(unreadable_file)], []).had_error is True

    def test_read_error_is_reported(
        self, unreadable_file: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        process_files([str(unreadable_file)], [])
        assert "Error reading" in capsys.readouterr().err


@pytest.mark.unit
class TestOutputFindings:
    def test_outputs_first_finding(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        output_findings([Finding("test.py", 1, "test_a", 0)])
        assert "test.py:1:test_a:0" in capsys.readouterr().out

    def test_outputs_every_finding(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        output_findings(
            [
                Finding("test.py", 1, "test_a", 0),
                Finding("test.py", 2, "test_b", 2),
            ]
        )
        assert "test.py:2:test_b:2" in capsys.readouterr().out

    def test_count_mode(self, capsys: pytest.CaptureFixture[str]) -> None:
        output_findings([Finding("test.py", 1, "test_a", 0)], count_mode=True)
        assert capsys.readouterr().out.strip() == "1"


@pytest.mark.unit
class TestDetermineExitCode:
    def test_returns_0_for_no_findings(self) -> None:
        result = ScanResult(findings=[], files_scanned=1, had_error=False)
        assert determine_exit_code(result) == 0

    def test_returns_1_for_findings(self) -> None:
        result = ScanResult(
            findings=[Finding("test.py", 1, "test_a", 0)],
            files_scanned=1,
            had_error=False,
        )
        assert determine_exit_code(result) == 1

    def test_returns_2_for_error(self) -> None:
        result = ScanResult(findings=[], files_scanned=0, had_error=True)
        assert determine_exit_code(result) == 2

    def test_warn_only_returns_0(self) -> None:
        result = ScanResult(
            findings=[Finding("test.py", 1, "test_a", 0)],
            files_scanned=1,
            had_error=False,
        )
        assert determine_exit_code(result, warn_only=True) == 0


@pytest.mark.unit
class TestMain:
    def test_exits_0_for_clean_file(
        self, test_file: MakeFile, run_cli: RunCli
    ) -> None:
        path = test_file("def test_a():\n    assert True\n", "test_clean.py")
        assert run_cli([str(path)])[0] == 0

    def test_exits_1_for_findings(
        self, test_file: MakeFile, run_cli: RunCli
    ) -> None:
        path = test_file("def test_a():\n    pass\n", "test_finding.py")
        assert run_cli([str(path)])[0] == 1

    def test_exits_2_for_missing_file(self, run_cli: RunCli) -> None:
        assert run_cli(["/nonexistent/path.py"])[0] == 2

    def test_verbose_shows_scanning(
        self, test_file: MakeFile, run_cli: RunCli
    ) -> None:
        path = test_file("def test_a():\n    assert True\n", "test_verbose.py")
        assert "Scanning" in run_cli([str(path), "--verbose"])[1]

    def test_verbose_shows_files_scanned(
        self, test_file: MakeFile, run_cli: RunCli
    ) -> None:
        path = test_file("def test_a():\n    assert True\n", "test_verbose.py")
        assert "Files scanned:" in run_cli([str(path), "--verbose"])[1]

    def test_verbose_with_exclude(
        self, test_file: MakeFile, run_cli: RunCli
    ) -> None:
        path = test_file("def test_a():\n    assert True\n", "test_excl.py")
        stdout = run_cli([str(path), "--verbose", "--exclude", "*.txt"])[1]
        assert "Excluding patterns:" in stdout

    def test_verbose_shows_errors(
        self, test_file: MakeFile, run_cli: RunCli
    ) -> None:
        path = test_file("def test_a():\n    assert True\n", "test_err.py")
        stdout = run_cli([str(path), "/nonexistent.py", "--verbose"])[1]
        assert "Errors occurred" in stdout

    def test_quiet_mode(self, test_file: MakeFile, run_cli: RunCli) -> None:
        path = test_file("def test_a():\n    pass\n", "test_quiet.py")
        assert run_cli([str(path), "--quiet"])[1] == ""

    def test_count_mode(self, test_file: MakeFile, run_cli: RunCli) -> None:
        path = test_file("def test_a():\n    pass\n", "test_count.py")
        assert run_cli([str(path), "--count"])[1].strip() == "1"

    def test_warn_only_exits_0(
        self, test_file: MakeFile, run_cli: RunCli
    ) -> None:
        path = test_file("def test_a():\n    pass\n", "test_warn.py")
        assert run_cli([str(path), "--warn-only"])[0] == 0

    def test_fail_fast(self, tmp_path: Path, run_cli: RunCli) -> None:
        (tmp_path / "test_a.py").write_text("def test_a():\n    pass\n")
        (tmp_path / "test_b.py").write_text("def test_b():\n    pass\n")
        stdout = run_cli([str(tmp_path), "--fail-fast"])[1]
        assert len([line for line in stdout.strip().split("\n") if line]) == 1
