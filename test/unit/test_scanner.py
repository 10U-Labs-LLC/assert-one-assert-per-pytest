"""Unit tests for the scanner module."""

from __future__ import annotations

import ast

import pytest

from assert_one_assert_per_pytest.scanner import (
    Finding,
    count_asserts,
    is_test_file,
    is_test_function,
    iter_test_functions,
    scan_file,
)


@pytest.mark.unit
class TestIsTestFunction:
    """Tests for is_test_function."""

    def test_returns_true_for_test_prefix(self) -> None:
        """Verify test_ prefix is recognized."""
        assert is_test_function("test_example") is True

    def test_returns_true_for_test_underscore_only(self) -> None:
        """Verify test_ alone is recognized."""
        assert is_test_function("test_") is True

    def test_returns_false_for_no_prefix(self) -> None:
        """Verify non-test names are rejected."""
        assert is_test_function("example") is False

    def test_returns_false_for_test_without_underscore(self) -> None:
        """Verify 'testing' without underscore is rejected."""
        assert is_test_function("testing") is False

    def test_returns_false_for_empty_string(self) -> None:
        """Verify empty string is rejected."""
        assert is_test_function("") is False


@pytest.mark.unit
class TestIsTestFile:
    """Tests for is_test_file."""

    def test_returns_true_for_test_prefix(self) -> None:
        """Verify test_ prefix files are recognized."""
        assert is_test_file("test_example.py") is True

    def test_returns_true_for_test_suffix(self) -> None:
        """Verify _test.py suffix files are recognized."""
        assert is_test_file("example_test.py") is True

    def test_returns_true_for_path_with_test_prefix(self) -> None:
        """Verify paths with test_ prefix are recognized."""
        assert is_test_file("tests/unit/test_example.py") is True

    def test_returns_false_for_non_test_file(self) -> None:
        """Verify non-test files are rejected."""
        assert is_test_file("example.py") is False

    def test_returns_false_for_conftest(self) -> None:
        """Verify conftest.py is not considered a test file."""
        assert is_test_file("conftest.py") is False


@pytest.mark.unit
class TestCountAsserts:
    """Tests for count_asserts."""

    def test_counts_single_assert(self) -> None:
        """Verify single assert is counted correctly."""
        code = """
def test_example():
    assert True
"""
        tree = ast.parse(code)
        func = tree.body[0]
        assert isinstance(func, ast.FunctionDef)
        assert count_asserts(func) == 1

    def test_counts_multiple_asserts(self) -> None:
        """Verify multiple asserts are counted correctly."""
        code = """
def test_example():
    assert True
    assert False
    assert 1 == 1
"""
        tree = ast.parse(code)
        func = tree.body[0]
        assert isinstance(func, ast.FunctionDef)
        assert count_asserts(func) == 3

    def test_counts_zero_asserts(self) -> None:
        """Verify zero asserts returns 0."""
        code = """
def test_example():
    x = 1
    print(x)
"""
        tree = ast.parse(code)
        func = tree.body[0]
        assert isinstance(func, ast.FunctionDef)
        assert count_asserts(func) == 0

    def test_ignores_nested_function_asserts(self) -> None:
        """Verify asserts in nested functions are not counted."""
        code = """
def test_example():
    assert True
    def helper():
        assert False
"""
        tree = ast.parse(code)
        func = tree.body[0]
        assert isinstance(func, ast.FunctionDef)
        assert count_asserts(func) == 1

    def test_ignores_nested_class_asserts(self) -> None:
        """Verify asserts in nested classes are not counted."""
        code = """
def test_example():
    assert True
    class Helper:
        def method(self):
            assert False
"""
        tree = ast.parse(code)
        func = tree.body[0]
        assert isinstance(func, ast.FunctionDef)
        assert count_asserts(func) == 1


@pytest.mark.unit
class TestScanFile:
    """Tests for scan_file."""

    def test_finds_test_with_zero_asserts(self) -> None:
        """Verify tests with zero asserts are found."""
        code = """
def test_example():
    pass
"""
        findings = scan_file("test_example.py", code)
        assert len(findings) == 1

    def test_finds_test_with_multiple_asserts(self) -> None:
        """Verify tests with multiple asserts are found."""
        code = """
def test_example():
    assert True
    assert False
"""
        findings = scan_file("test_example.py", code)
        assert len(findings) == 1

    def test_no_findings_for_single_assert(self) -> None:
        """Verify tests with exactly one assert have no findings."""
        code = """
def test_example():
    assert True
"""
        findings = scan_file("test_example.py", code)
        assert len(findings) == 0

    def test_ignores_non_test_functions(self) -> None:
        """Verify non-test functions are ignored."""
        code = """
def helper():
    pass

def test_example():
    assert True
"""
        findings = scan_file("test_example.py", code)
        assert len(findings) == 0

    def test_finds_multiple_violations(self) -> None:
        """Verify multiple violations are found."""
        code = """
def test_no_asserts():
    pass

def test_one_assert():
    assert True

def test_many_asserts():
    assert True
    assert False
"""
        findings = scan_file("test_example.py", code)
        assert len(findings) == 2

    def test_handles_async_test_functions(self) -> None:
        """Verify async test functions are handled."""
        code = """
async def test_async():
    pass
"""
        findings = scan_file("test_example.py", code)
        assert len(findings) == 1

    def test_handles_class_test_methods(self) -> None:
        """Verify test methods in classes are handled."""
        code = """
class TestExample:
    def test_method(self):
        pass
"""
        findings = scan_file("test_example.py", code)
        assert len(findings) == 1

    def test_raises_on_syntax_error(self) -> None:
        """Verify syntax errors are raised."""
        code = "def test_example( broken syntax"
        with pytest.raises(SyntaxError):
            scan_file("test_example.py", code)


@pytest.mark.unit
class TestFinding:
    """Tests for Finding dataclass."""

    def test_str_format(self) -> None:
        """Verify string format is correct."""
        finding = Finding(
            path="test_example.py",
            line_number=10,
            function_name="test_something",
            assert_count=0,
        )
        assert str(finding) == "test_example.py:10:test_something:0"

    def test_frozen(self) -> None:
        """Verify dataclass is frozen."""
        finding = Finding(
            path="test_example.py",
            line_number=10,
            function_name="test_something",
            assert_count=0,
        )
        with pytest.raises(AttributeError):
            finding.path = "other.py"  # type: ignore[misc]


@pytest.mark.unit
class TestIterTestFunctions:
    """Tests for iter_test_functions."""

    def test_yields_test_functions(self) -> None:
        """Verify test functions are yielded."""
        code = """
def test_a():
    assert True

def test_b():
    pass
"""
        results = list(iter_test_functions("test.py", code))
        assert len(results) == 2

    def test_yields_function_name_and_line(self) -> None:
        """Verify function name and line are correct."""
        code = """
def test_example():
    assert True
"""
        results = list(iter_test_functions("test.py", code))
        assert results[0][0] == "test_example"
        assert results[0][1] == 2

    def test_yields_assert_count(self) -> None:
        """Verify assert count is correct."""
        code = """
def test_multiple():
    assert True
    assert False
"""
        results = list(iter_test_functions("test.py", code))
        assert results[0][2] == 2

    def test_ignores_non_test_functions(self) -> None:
        """Verify non-test functions are ignored."""
        code = """
def helper():
    pass

def test_only():
    assert True
"""
        results = list(iter_test_functions("test.py", code))
        assert len(results) == 1
        assert results[0][0] == "test_only"

    def test_handles_async_functions(self) -> None:
        """Verify async test functions are handled."""
        code = """
async def test_async():
    assert True
"""
        results = list(iter_test_functions("test.py", code))
        assert len(results) == 1
        assert results[0][0] == "test_async"
