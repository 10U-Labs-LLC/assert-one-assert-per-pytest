"""Core scanning logic for detecting pytest tests with incorrect assert counts."""

from __future__ import annotations

import ast
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator


@dataclass(frozen=True)
class Finding:
    """Represents a pytest test function with an incorrect number of assert statements."""

    path: str
    line_number: int
    function_name: str
    assert_count: int

    def __str__(self) -> str:
        """Format as path:line:function:count."""
        return f"{self.path}:{self.line_number}:{self.function_name}:{self.assert_count}"


def _is_pytest_assertion_context(node: ast.With) -> bool:
    """Check if a with statement uses pytest.raises or pytest.warns."""
    for item in node.items:
        ctx = item.context_expr
        if isinstance(ctx, ast.Call):
            func = ctx.func
            # Check for pytest.raises(...) or pytest.warns(...)
            if isinstance(func, ast.Attribute):
                if func.attr in ("raises", "warns"):
                    if isinstance(func.value, ast.Name) and func.value.id == "pytest":
                        return True
    return False


class AssertCounter(ast.NodeVisitor):
    """AST visitor that counts assert statements in a function body.

    Only counts asserts at the immediate level of the function, not in nested
    functions or classes defined within the test.

    Also counts pytest.raises() and pytest.warns() context managers as assertions.
    """

    def __init__(self) -> None:
        self.count = 0

    def generic_visit(self, node: ast.AST) -> None:
        """Visit nodes and count asserts, skipping nested scopes."""
        if isinstance(node, ast.Assert):
            self.count += 1
        elif isinstance(node, ast.With) and _is_pytest_assertion_context(node):
            self.count += 1
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            # Don't descend into nested functions or classes
            return
        else:
            super().generic_visit(node)


def count_asserts(function_node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    """Count assert statements in a function body.

    Only counts asserts at the immediate level of the function, not in nested
    functions or classes defined within the test.
    """
    counter = AssertCounter()
    for child in function_node.body:
        counter.visit(child)
    return counter.count


def is_test_function(name: str) -> bool:
    """Check if a function name indicates a pytest test function."""
    return name.startswith("test_")


def is_test_file(path: str) -> bool:
    """Check if a file path indicates a pytest test file."""
    basename = os.path.basename(path)
    return basename.startswith("test_") or basename.endswith("_test.py")


class TestFunctionFinder(ast.NodeVisitor):
    """AST visitor that finds all test functions and their assert counts."""

    def __init__(self, path: str) -> None:
        self.path = path
        self.findings: list[Finding] = []

    def _check_function(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> None:
        """Check a function for the correct number of asserts."""
        if not is_test_function(node.name):
            return

        assert_count = count_asserts(node)
        if assert_count != 1:
            self.findings.append(
                Finding(
                    path=self.path,
                    line_number=node.lineno,
                    function_name=node.name,
                    assert_count=assert_count,
                )
            )

    def generic_visit(self, node: ast.AST) -> None:
        """Visit nodes to find test functions."""
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            self._check_function(node)
        super().generic_visit(node)


def scan_file(path: str, content: str) -> list[Finding]:
    """Scan a Python file for pytest tests with incorrect assert counts.

    Args:
        path: The file path (used for error reporting).
        content: The file content to parse.

    Returns:
        List of findings for tests that don't have exactly one assert.

    Raises:
        SyntaxError: If the file cannot be parsed as Python.
    """
    tree = ast.parse(content, filename=path)
    finder = TestFunctionFinder(path)
    finder.visit(tree)
    return finder.findings


def iter_test_functions(
    path: str, content: str
) -> Iterator[tuple[str, int, int]]:
    """Iterate over test functions in a file.

    Yields:
        Tuples of (function_name, line_number, assert_count).

    Raises:
        SyntaxError: If the file cannot be parsed as Python.
    """
    tree = ast.parse(content, filename=path)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if is_test_function(node.name):
                assert_count = count_asserts(node)
                yield (node.name, node.lineno, assert_count)
