"""Unit tests for the CLI module."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

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
    main,
    output_findings,
    parse_patterns,
    process_files,
)
from assert_one_assert_per_pytest.scanner import Finding

if TYPE_CHECKING:
    from collections.abc import Callable


@pytest.mark.unit
class TestCreateParser:
    """Tests for create_parser."""

    def test_requires_files_argument(self) -> None:
        """Verify files argument is required."""
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_accepts_single_file(self) -> None:
        """Verify single file argument is accepted."""
        parser = create_parser()
        args = parser.parse_args(["test_example.py"])
        assert args.files == ["test_example.py"]

    def test_accepts_multiple_files(self) -> None:
        """Verify multiple file arguments are accepted."""
        parser = create_parser()
        args = parser.parse_args(["test_a.py", "test_b.py"])
        assert args.files == ["test_a.py", "test_b.py"]

    def test_accepts_exclude_option(self) -> None:
        """Verify exclude option is parsed correctly."""
        parser = create_parser()
        args = parser.parse_args(["tests/", "--exclude", "**/conftest.py"])
        assert args.exclude == "**/conftest.py"

    def test_quiet_flag(self) -> None:
        """Verify quiet flag is recognized."""
        parser = create_parser()
        args = parser.parse_args(["tests/", "--quiet"])
        assert args.quiet is True

    def test_count_flag(self) -> None:
        """Verify count flag is recognized."""
        parser = create_parser()
        args = parser.parse_args(["tests/", "--count"])
        assert args.count is True

    def test_verbose_flag(self) -> None:
        """Verify verbose flag is recognized."""
        parser = create_parser()
        args = parser.parse_args(["tests/", "--verbose"])
        assert args.verbose is True

    def test_fail_fast_flag(self) -> None:
        """Verify fail-fast flag is recognized."""
        parser = create_parser()
        args = parser.parse_args(["tests/", "--fail-fast"])
        assert args.fail_fast is True

    def test_warn_only_flag(self) -> None:
        """Verify warn-only flag is recognized."""
        parser = create_parser()
        args = parser.parse_args(["tests/", "--warn-only"])
        assert args.warn_only is True

    def test_output_modes_mutually_exclusive(self) -> None:
        """Verify quiet and count cannot be used together."""
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["tests/", "--quiet", "--count"])

    def test_behavior_modes_mutually_exclusive(self) -> None:
        """Verify fail-fast and warn-only cannot be used together."""
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["tests/", "--fail-fast", "--warn-only"])


@pytest.mark.unit
class TestParsePatterns:
    """Tests for parse_patterns."""

    def test_returns_empty_for_none(self) -> None:
        """Verify None returns empty list."""
        assert parse_patterns(None) == []

    def test_returns_empty_for_empty_string(self) -> None:
        """Verify empty string returns empty list."""
        assert parse_patterns("") == []

    def test_parses_single_pattern(self) -> None:
        """Verify single pattern is parsed correctly."""
        assert parse_patterns("*.py") == ["*.py"]

    def test_parses_multiple_patterns(self) -> None:
        """Verify multiple patterns are parsed correctly."""
        patterns = parse_patterns("*.py,*.txt,*.md")
        assert patterns == ["*.py", "*.txt", "*.md"]

    def test_strips_whitespace(self) -> None:
        """Verify whitespace is stripped from patterns."""
        patterns = parse_patterns(" *.py , *.txt ")
        assert patterns == ["*.py", "*.txt"]

    def test_ignores_empty_entries(self) -> None:
        """Verify empty entries are ignored."""
        patterns = parse_patterns("*.py,,*.txt,")
        assert patterns == ["*.py", "*.txt"]


@pytest.mark.unit
class TestIsGlobPattern:
    """Tests for _is_glob_pattern."""

    def test_detects_asterisk(self) -> None:
        """Verify asterisk is detected."""
        assert _is_glob_pattern("*.py") is True

    def test_detects_question_mark(self) -> None:
        """Verify question mark is detected."""
        assert _is_glob_pattern("test?.py") is True

    def test_detects_bracket(self) -> None:
        """Verify bracket is detected."""
        assert _is_glob_pattern("test[0-9].py") is True

    def test_regular_path_is_not_glob(self) -> None:
        """Verify regular path is not a glob."""
        assert _is_glob_pattern("test/example.py") is False


@pytest.mark.unit
class TestExpandDirectory:
    """Tests for _expand_directory."""

    def test_finds_test_files(self, tmp_path: Path) -> None:
        """Verify test files are found."""
        (tmp_path / "test_example.py").write_text("")
        files = _expand_directory(str(tmp_path))
        assert len(files) == 1

    def test_finds_test_suffix_files(self, tmp_path: Path) -> None:
        """Verify _test.py suffix files are found."""
        (tmp_path / "example_test.py").write_text("")
        files = _expand_directory(str(tmp_path))
        assert len(files) == 1

    def test_ignores_non_test_files(self, tmp_path: Path) -> None:
        """Verify non-test files are ignored."""
        (tmp_path / "helper.py").write_text("")
        files = _expand_directory(str(tmp_path))
        assert len(files) == 0

    def test_recurses_into_subdirectories(self, tmp_path: Path) -> None:
        """Verify subdirectories are scanned."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "test_nested.py").write_text("")
        files = _expand_directory(str(tmp_path))
        assert len(files) == 1

    def test_skips_hidden_directories(self, tmp_path: Path) -> None:
        """Verify hidden directories are skipped."""
        hidden = tmp_path / ".hidden"
        hidden.mkdir()
        (hidden / "test_hidden.py").write_text("")
        files = _expand_directory(str(tmp_path))
        assert len(files) == 0


@pytest.mark.unit
class TestExpandGlob:
    """Tests for _expand_glob."""

    def test_returns_matching_files(self, tmp_path: Path) -> None:
        """Verify matching files are returned."""
        (tmp_path / "test_a.py").write_text("")
        (tmp_path / "test_b.py").write_text("")
        files, found = _expand_glob(f"{tmp_path}/test_*.py")
        assert found is True
        assert len(files) == 2

    def test_returns_empty_for_no_matches(self) -> None:
        """Verify empty list for no matches."""
        files, found = _expand_glob("/nonexistent/path/*.py")
        assert found is False
        assert not files

    def test_expands_directories_in_glob(self, tmp_path: Path) -> None:
        """Verify directories matched by glob are expanded."""
        subdir = tmp_path / "tests"
        subdir.mkdir()
        (subdir / "test_example.py").write_text("")
        files, found = _expand_glob(str(subdir))
        assert found is True
        assert len(files) == 1


@pytest.mark.unit
class TestIterFiles:
    """Tests for _iter_files."""

    def test_handles_single_file(self, tmp_path: Path) -> None:
        """Verify single file is returned."""
        test_file = tmp_path / "test_example.py"
        test_file.write_text("")
        files, missing = _iter_files([str(test_file)])
        assert len(files) == 1
        assert not missing

    def test_handles_directory(self, tmp_path: Path) -> None:
        """Verify directory is expanded."""
        (tmp_path / "test_example.py").write_text("")
        files, _ = _iter_files([str(tmp_path)])
        assert len(files) == 1

    def test_handles_glob_pattern(self, tmp_path: Path) -> None:
        """Verify glob patterns are expanded."""
        (tmp_path / "test_a.py").write_text("")
        (tmp_path / "test_b.py").write_text("")
        files, _ = _iter_files([f"{tmp_path}/test_*.py"])
        assert len(files) == 2

    def test_reports_missing_paths(self) -> None:
        """Verify missing paths are reported."""
        files, missing = _iter_files(["/nonexistent/path.py"])
        assert not files
        assert len(missing) == 1

    def test_reports_missing_glob(self) -> None:
        """Verify non-matching globs are reported as missing."""
        files, missing = _iter_files(["/nonexistent/*.py"])
        assert not files
        assert len(missing) == 1

    def test_deduplicates_files(self, tmp_path: Path) -> None:
        """Verify duplicate files are deduplicated."""
        test_file = tmp_path / "test_example.py"
        test_file.write_text("")
        files, _ = _iter_files([str(test_file), str(test_file)])
        assert len(files) == 1


@pytest.mark.unit
class TestShouldSkipFile:
    """Tests for _should_skip_file."""

    def test_no_patterns_returns_false(self) -> None:
        """Verify no patterns means no skip."""
        assert _should_skip_file("test.py", []) is False

    def test_matches_full_path(self) -> None:
        """Verify full path matching works."""
        assert _should_skip_file("path/to/test.py", ["path/to/test.py"]) is True

    def test_matches_filename(self) -> None:
        """Verify filename matching works."""
        assert _should_skip_file("path/to/conftest.py", ["conftest.py"]) is True

    def test_matches_glob_pattern(self) -> None:
        """Verify glob pattern matching works."""
        assert _should_skip_file("path/to/test_skip.py", ["**/test_skip.py"]) is True

    def test_no_match_returns_false(self) -> None:
        """Verify non-matching patterns don't skip."""
        assert _should_skip_file("test.py", ["other.py"]) is False


@pytest.mark.unit
class TestProcessFiles:
    """Tests for process_files."""

    def test_processes_test_file(
        self, test_file: Callable[[str, str], Path]
    ) -> None:
        """Verify test files are processed."""
        path = test_file("def test_a():\n    pass\n", "test_example.py")
        result = process_files([str(path)], [])
        assert result.files_scanned == 1
        assert len(result.findings) == 1

    def test_skips_non_python_files(
        self, test_file: Callable[[str, str], Path]
    ) -> None:
        """Verify non-Python files are skipped."""
        path = test_file("content", "readme.txt")
        result = process_files([str(path)], [])
        assert result.files_scanned == 0

    def test_skips_non_test_files(
        self, test_file: Callable[[str, str], Path]
    ) -> None:
        """Verify non-test files are skipped."""
        path = test_file("def helper():\n    pass\n", "helper.py")
        result = process_files([str(path)], [])
        assert result.files_scanned == 0

    def test_respects_exclude_patterns(
        self, test_file: Callable[[str, str], Path]
    ) -> None:
        """Verify exclude patterns are respected."""
        path = test_file("def test_a():\n    pass\n", "test_skip.py")
        result = process_files([str(path)], ["**/test_skip.py"])
        assert result.files_scanned == 0

    def test_handles_syntax_errors(
        self, test_file: Callable[[str, str], Path]
    ) -> None:
        """Verify syntax errors are handled."""
        path = test_file("def test_a( broken", "test_broken.py")
        result = process_files([str(path)], [])
        assert result.had_error is True

    def test_fail_fast_stops_early(self, tmp_path: Path) -> None:
        """Verify fail-fast stops after first finding."""
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
        test_file: Callable[[str, str], Path],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Verify verbose output is printed."""
        path = test_file("def test_a():\n    assert True\n", "test_verbose.py")
        process_files([str(path)], [], verbose=True)
        captured = capsys.readouterr()
        assert "Scanning:" in captured.out

    def test_verbose_shows_excluded(
        self,
        test_file: Callable[[str, str], Path],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Verify verbose output shows excluded files."""
        path = test_file("def test_a():\n    pass\n", "test_skip.py")
        process_files([str(path)], ["**/test_skip.py"], verbose=True)
        captured = capsys.readouterr()
        assert "Skipping (excluded):" in captured.out

    def test_verbose_shows_findings(
        self,
        test_file: Callable[[str, str], Path],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Verify verbose output shows findings."""
        path = test_file("def test_a():\n    pass\n", "test_findings.py")
        process_files([str(path)], [], verbose=True)
        captured = capsys.readouterr()
        assert "Found:" in captured.out

    def test_handles_read_errors(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Verify read errors are handled gracefully."""
        test_file = tmp_path / "test_unreadable.py"
        test_file.write_text("def test_a():\n    pass\n")
        test_file.chmod(0o000)
        try:
            result = process_files([str(test_file)], [])
            assert result.had_error is True
            captured = capsys.readouterr()
            assert "Error reading" in captured.err
        finally:
            test_file.chmod(0o644)


@pytest.mark.unit
class TestOutputFindings:
    """Tests for output_findings."""

    def test_outputs_findings(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Verify findings are output."""
        findings = [
            Finding("test.py", 1, "test_a", 0),
            Finding("test.py", 2, "test_b", 2),
        ]
        output_findings(findings)
        captured = capsys.readouterr()
        assert "test.py:1:test_a:0" in captured.out
        assert "test.py:2:test_b:2" in captured.out

    def test_count_mode(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Verify count mode outputs only count."""
        findings = [Finding("test.py", 1, "test_a", 0)]
        output_findings(findings, count_mode=True)
        captured = capsys.readouterr()
        assert captured.out.strip() == "1"


@pytest.mark.unit
class TestDetermineExitCode:
    """Tests for determine_exit_code."""

    def test_returns_0_for_no_findings(self) -> None:
        """Verify exit code 0 when no findings."""
        result = ScanResult(findings=[], files_scanned=1, had_error=False)
        assert determine_exit_code(result) == 0

    def test_returns_1_for_findings(self) -> None:
        """Verify exit code 1 when findings exist."""
        result = ScanResult(
            findings=[Finding("test.py", 1, "test_a", 0)],
            files_scanned=1,
            had_error=False,
        )
        assert determine_exit_code(result) == 1

    def test_returns_2_for_error(self) -> None:
        """Verify exit code 2 when error occurred."""
        result = ScanResult(findings=[], files_scanned=0, had_error=True)
        assert determine_exit_code(result) == 2

    def test_warn_only_returns_0(self) -> None:
        """Verify warn-only always returns 0."""
        result = ScanResult(
            findings=[Finding("test.py", 1, "test_a", 0)],
            files_scanned=1,
            had_error=False,
        )
        assert determine_exit_code(result, warn_only=True) == 0


@pytest.mark.unit
class TestMain:
    """Tests for main function."""

    def test_exits_0_for_clean_file(
        self, test_file: Callable[[str, str], Path]
    ) -> None:
        """Verify exit 0 when file is clean."""
        path = test_file("def test_a():\n    assert True\n", "test_clean.py")
        with pytest.raises(SystemExit) as exc_info:
            main([str(path)])
        assert exc_info.value.code == 0

    def test_exits_1_for_findings(
        self, test_file: Callable[[str, str], Path]
    ) -> None:
        """Verify exit 1 when findings exist."""
        path = test_file("def test_a():\n    pass\n", "test_finding.py")
        with pytest.raises(SystemExit) as exc_info:
            main([str(path)])
        assert exc_info.value.code == 1

    def test_exits_2_for_missing_file(self) -> None:
        """Verify exit 2 when file is missing."""
        with pytest.raises(SystemExit) as exc_info:
            main(["/nonexistent/path.py"])
        assert exc_info.value.code == 2

    def test_verbose_output(
        self,
        test_file: Callable[[str, str], Path],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Verify verbose output format."""
        path = test_file("def test_a():\n    assert True\n", "test_verbose.py")
        with pytest.raises(SystemExit):
            main([str(path), "--verbose"])
        captured = capsys.readouterr()
        assert "Scanning" in captured.out
        assert "Files scanned:" in captured.out

    def test_verbose_with_exclude(
        self,
        test_file: Callable[[str, str], Path],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Verify verbose shows exclude patterns."""
        path = test_file("def test_a():\n    assert True\n", "test_excl.py")
        with pytest.raises(SystemExit):
            main([str(path), "--verbose", "--exclude", "*.txt"])
        captured = capsys.readouterr()
        assert "Excluding patterns:" in captured.out

    def test_verbose_shows_errors(
        self,
        test_file: Callable[[str, str], Path],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Verify verbose shows error message."""
        path = test_file("def test_a():\n    assert True\n", "test_err.py")
        with pytest.raises(SystemExit):
            main([str(path), "/nonexistent.py", "--verbose"])
        captured = capsys.readouterr()
        assert "Errors occurred" in captured.out

    def test_quiet_mode(
        self,
        test_file: Callable[[str, str], Path],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Verify quiet mode produces no stdout."""
        path = test_file("def test_a():\n    pass\n", "test_quiet.py")
        with pytest.raises(SystemExit):
            main([str(path), "--quiet"])
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_count_mode(
        self,
        test_file: Callable[[str, str], Path],
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Verify count mode outputs count."""
        path = test_file("def test_a():\n    pass\n", "test_count.py")
        with pytest.raises(SystemExit):
            main([str(path), "--count"])
        captured = capsys.readouterr()
        assert captured.out.strip() == "1"

    def test_warn_only_exits_0(
        self, test_file: Callable[[str, str], Path]
    ) -> None:
        """Verify warn-only exits 0 even with findings."""
        path = test_file("def test_a():\n    pass\n", "test_warn.py")
        with pytest.raises(SystemExit) as exc_info:
            main([str(path), "--warn-only"])
        assert exc_info.value.code == 0

    def test_fail_fast(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Verify fail-fast stops after first finding."""
        (tmp_path / "test_a.py").write_text("def test_a():\n    pass\n")
        (tmp_path / "test_b.py").write_text("def test_b():\n    pass\n")
        with pytest.raises(SystemExit):
            main([str(tmp_path), "--fail-fast"])
        captured = capsys.readouterr()
        lines = [line for line in captured.out.strip().split("\n") if line]
        assert len(lines) == 1
