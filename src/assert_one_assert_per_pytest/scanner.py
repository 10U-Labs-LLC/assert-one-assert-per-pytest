from __future__ import annotations

import ast
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
    conjunction: bool = False

    def __str__(self) -> str:
        suffix = ":conjunction" if self.conjunction else ""
        return (
            f"{self.path}:{self.line_number}:{self.function_name}"
            f":{self.assert_count}{suffix}"
        )


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


def _conjunct_count(node: ast.Assert) -> int:
    test = node.test
    if isinstance(test, ast.BoolOp) and isinstance(test.op, ast.And):
        return len(test.values)
    return 0


class AssertCounter(ast.NodeVisitor):
    def __init__(self) -> None:
        self.count = 0
        self.conjunctions: list[tuple[int, int]] = []

    def _visit_assert(self, node: ast.Assert) -> None:
        self.count += 1
        conjuncts = _conjunct_count(node)
        if conjuncts:
            self.conjunctions.append((node.lineno, conjuncts))

    def generic_visit(self, node: ast.AST) -> None:
        if isinstance(node, ast.Assert):
            self._visit_assert(node)
        elif isinstance(node, ast.With) and _is_pytest_assertion_context(node):
            self.count += 1
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            return
        else:
            super().generic_visit(node)


def _visit_test_body(
    function_node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> AssertCounter:
    counter = AssertCounter()
    for child in function_node.body:
        counter.visit(child)
    return counter


def count_asserts(function_node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    return _visit_test_body(function_node).count


def find_conjunctions(
    function_node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> list[tuple[int, int]]:
    return _visit_test_body(function_node).conjunctions


def is_test_function(name: str) -> bool:
    return name.startswith("test_")


def is_pytest_fixture(
    function_node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> bool:
    for decorator in function_node.decorator_list:
        func = decorator.func if isinstance(decorator, ast.Call) else decorator
        if isinstance(func, ast.Attribute) and func.attr == "fixture":
            return True
        if isinstance(func, ast.Name) and func.id == "fixture":
            return True
    return False


class TestFunctionFinder(ast.NodeVisitor):
    def __init__(self, path: str) -> None:
        self.path = path
        self.findings: list[Finding] = []

    def _record(
        self,
        line_number: int,
        function_name: str,
        assert_count: int,
        conjunction: bool = False,
    ) -> None:
        self.findings.append(
            Finding(
                path=self.path,
                line_number=line_number,
                function_name=function_name,
                assert_count=assert_count,
                conjunction=conjunction,
            )
        )

    def _check_function(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> None:
        if not is_test_function(node.name) or is_pytest_fixture(node):
            return

        assert_count = count_asserts(node)
        if assert_count != 1:
            self._record(node.lineno, node.name, assert_count)

        for line_number, conjuncts in find_conjunctions(node):
            self._record(line_number, node.name, conjuncts, conjunction=True)

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
            if is_test_function(node.name) and not is_pytest_fixture(node):
                assert_count = count_asserts(node)
                yield (node.name, node.lineno, assert_count)
