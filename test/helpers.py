from __future__ import annotations

import ast
import subprocess
import sys


def parse_function(code: str) -> ast.FunctionDef:
    node = ast.parse(code).body[0]
    if not isinstance(node, ast.FunctionDef):
        raise TypeError(node)
    return node


def run_tool(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "assert_one_assert_per_pytest", *args],
        capture_output=True,
        text=True,
        check=False,
    )
