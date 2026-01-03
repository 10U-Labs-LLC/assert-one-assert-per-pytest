"""Unit tests for the scanner module."""

from __future__ import annotations

import pytest

from assert_one_assert_per_pytest.scanner import (
    Finding,
    count_asserts,
    is_test_file,
    is_test_function,
    scan_file,
)


@pytest.mark.unit
class TestIsTestFunction:
    """Tests for is_test_function."""

    def test_returns_true_for_test_prefix(self) -> None:
        assert is_test_function("test_example") is True

    def test_returns_true_for_test_underscore_only(self) -> None:
        assert is_test_function("test_") is True

    def test_returns_false_for_no_prefix(self) -> None:
        assert is_test_function("example") is False

    def test_returns_false_for_test_without_underscore(self) -> None:
        assert is_test_function("testing") is False

    def test_returns_false_for_empty_string(self) -> None:
        assert is_test_function("") is False


@pytest.mark.unit
class TestIsTestFile:
    """Tests for is_test_file."""

    def test_returns_true_for_test_prefix(self) -> None:
        assert is_test_file("test_example.py") is True

    def test_returns_true_for_test_suffix(self) -> None:
        assert is_test_file("example_test.py") is True

    def test_returns_true_for_path_with_test_prefix(self) -> None:
        assert is_test_file("tests/unit/test_example.py") is True

    def test_returns_false_for_non_test_file(self) -> None:
        assert is_test_file("example.py") is False

    def test_returns_false_for_conftest(self) -> None:
        assert is_test_file("conftest.py") is False


@pytest.mark.unit
class TestCountAsserts:
    """Tests for count_asserts."""

    def test_counts_single_assert(self) -> None:
        import ast

        code = """
def test_example():
    assert True
"""
        tree = ast.parse(code)
        func = tree.body[0]
        assert count_asserts(func) == 1

    def test_counts_multiple_asserts(self) -> None:
        import ast

        code = """
def test_example():
    assert True
    assert False
    assert 1 == 1
"""
        tree = ast.parse(code)
        func = tree.body[0]
        assert count_asserts(func) == 3

    def test_counts_zero_asserts(self) -> None:
        import ast

        code = """
def test_example():
    x = 1
    print(x)
"""
        tree = ast.parse(code)
        func = tree.body[0]
        assert count_asserts(func) == 0

    def test_ignores_nested_function_asserts(self) -> None:
        import ast

        code = """
def test_example():
    assert True
    def helper():
        assert False
"""
        tree = ast.parse(code)
        func = tree.body[0]
        assert count_asserts(func) == 1

    def test_ignores_nested_class_asserts(self) -> None:
        import ast

        code = """
def test_example():
    assert True
    class Helper:
        def method(self):
            assert False
"""
        tree = ast.parse(code)
        func = tree.body[0]
        assert count_asserts(func) == 1


@pytest.mark.unit
class TestScanFile:
    """Tests for scan_file."""

    def test_finds_test_with_zero_asserts(self) -> None:
        code = """
def test_example():
    pass
"""
        findings = scan_file("test_example.py", code)
        assert len(findings) == 1
        assert findings[0].function_name == "test_example"
        assert findings[0].assert_count == 0

    def test_finds_test_with_multiple_asserts(self) -> None:
        code = """
def test_example():
    assert True
    assert False
"""
        findings = scan_file("test_example.py", code)
        assert len(findings) == 1
        assert findings[0].function_name == "test_example"
        assert findings[0].assert_count == 2

    def test_no_findings_for_single_assert(self) -> None:
        code = """
def test_example():
    assert True
"""
        findings = scan_file("test_example.py", code)
        assert len(findings) == 0

    def test_ignores_non_test_functions(self) -> None:
        code = """
def helper():
    pass

def test_example():
    assert True
"""
        findings = scan_file("test_example.py", code)
        assert len(findings) == 0

    def test_finds_multiple_violations(self) -> None:
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
        names = {f.function_name for f in findings}
        assert names == {"test_no_asserts", "test_many_asserts"}

    def test_handles_async_test_functions(self) -> None:
        code = """
async def test_async():
    pass
"""
        findings = scan_file("test_example.py", code)
        assert len(findings) == 1
        assert findings[0].function_name == "test_async"

    def test_handles_class_test_methods(self) -> None:
        code = """
class TestExample:
    def test_method(self):
        pass
"""
        findings = scan_file("test_example.py", code)
        assert len(findings) == 1
        assert findings[0].function_name == "test_method"

    def test_raises_on_syntax_error(self) -> None:
        code = "def test_example( broken syntax"
        with pytest.raises(SyntaxError):
            scan_file("test_example.py", code)


@pytest.mark.unit
class TestFinding:
    """Tests for Finding dataclass."""

    def test_str_format(self) -> None:
        finding = Finding(
            path="test_example.py",
            line_number=10,
            function_name="test_something",
            assert_count=0,
        )
        assert str(finding) == "test_example.py:10:test_something:0"

    def test_frozen(self) -> None:
        finding = Finding(
            path="test_example.py",
            line_number=10,
            function_name="test_something",
            assert_count=0,
        )
        with pytest.raises(AttributeError):
            finding.path = "other.py"
