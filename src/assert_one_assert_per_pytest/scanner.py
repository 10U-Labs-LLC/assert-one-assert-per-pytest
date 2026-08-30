from __future__ import annotations

import ast
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator


@dataclass(frozen=True)
class Finding:
    path: str
    line_number: int
    function_name: str
    assert_count: int

    def __str__(self) -> str:
        return f"{self.path}:{self.line_number}:{self.function_name}:{self.assert_count}"


def _is_pytest_assertion_context(node: ast.With) -> bool:
    for item in node.items:
        ctx = item.context_expr
        if isinstance(ctx, ast.Call):
            func = ctx.func
            if isinstance(func, ast.Attribute):
                if func.attr in ("raises", "warns"):
                    if isinstance(func.value, ast.Name) and func.value.id == "pytest":
                        return True
    return False


class AssertCounter(ast.NodeVisitor):
    def __init__(self) -> None:
        self.count = 0

    def generic_visit(self, node: ast.AST) -> None:
        if isinstance(node, ast.Assert):
            self.count += 1
        elif isinstance(node, ast.With) and _is_pytest_assertion_context(node):
            self.count += 1
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            return
        else:
            super().generic_visit(node)


def count_asserts(function_node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    counter = AssertCounter()
    for child in function_node.body:
        counter.visit(child)
    return counter.count


def is_test_function(name: str) -> bool:
    return name.startswith("test_")


def is_test_file(path: str) -> bool:
    basename = os.path.basename(path)
    return basename.startswith("test_") or basename.endswith("_test.py")


class TestFunctionFinder(ast.NodeVisitor):
    def __init__(self, path: str) -> None:
        self.path = path
        self.findings: list[Finding] = []

    def _check_function(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> None:
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
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            self._check_function(node)
        super().generic_visit(node)


def scan_file(path: str, content: str) -> list[Finding]:
    tree = ast.parse(content, filename=path)
    finder = TestFunctionFinder(path)
    finder.visit(tree)
    return finder.findings


def iter_test_functions(
    path: str, content: str
) -> Iterator[tuple[str, int, int]]:
    tree = ast.parse(content, filename=path)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if is_test_function(node.name):
                assert_count = count_asserts(node)
                yield (node.name, node.lineno, assert_count)
