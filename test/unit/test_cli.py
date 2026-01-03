"""Unit tests for the CLI module."""

from __future__ import annotations

import pytest

from assert_one_assert_per_pytest.cli import (
    create_parser,
    parse_patterns,
)


@pytest.mark.unit
class TestCreateParser:
    """Tests for create_parser."""

    def test_requires_files_argument(self) -> None:
        parser = create_parser()
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_accepts_single_file(self) -> None:
        parser = create_parser()
        args = parser.parse_args(["test_example.py"])
        assert args.files == ["test_example.py"]

    def test_accepts_multiple_files(self) -> None:
        parser = create_parser()
        args = parser.parse_args(["test_a.py", "test_b.py"])
        assert args.files == ["test_a.py", "test_b.py"]

    def test_accepts_exclude_option(self) -> None:
        parser = create_parser()
        args = parser.parse_args(["tests/", "--exclude", "**/conftest.py"])
        assert args.exclude == "**/conftest.py"

    def test_quiet_flag(self) -> None:
        parser = create_parser()
        args = parser.parse_args(["tests/", "--quiet"])
        assert args.quiet is True

    def test_count_flag(self) -> None:
        parser = create_parser()
        args = parser.parse_args(["tests/", "--count"])
        assert args.count is True

    def test_json_flag(self) -> None:
        parser = create_parser()
        args = parser.parse_args(["tests/", "--json"])
        assert args.json is True

    def test_verbose_flag(self) -> None:
        parser = create_parser()
        args = parser.parse_args(["tests/", "--verbose"])
        assert args.verbose is True

    def test_fail_fast_flag(self) -> None:
        parser = create_parser()
        args = parser.parse_args(["tests/", "--fail-fast"])
        assert args.fail_fast is True

    def test_warn_only_flag(self) -> None:
        parser = create_parser()
        args = parser.parse_args(["tests/", "--warn-only"])
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
    """Tests for parse_patterns."""

    def test_returns_empty_for_none(self) -> None:
        assert parse_patterns(None) == []

    def test_returns_empty_for_empty_string(self) -> None:
        assert parse_patterns("") == []

    def test_parses_single_pattern(self) -> None:
        assert parse_patterns("*.py") == ["*.py"]

    def test_parses_multiple_patterns(self) -> None:
        patterns = parse_patterns("*.py,*.txt,*.md")
        assert patterns == ["*.py", "*.txt", "*.md"]

    def test_strips_whitespace(self) -> None:
        patterns = parse_patterns(" *.py , *.txt ")
        assert patterns == ["*.py", "*.txt"]

    def test_ignores_empty_entries(self) -> None:
        patterns = parse_patterns("*.py,,*.txt,")
        assert patterns == ["*.py", "*.txt"]
