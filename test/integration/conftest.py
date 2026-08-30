from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from test.samples import NO_ASSERTS

import pytest

RunCli = Callable[[list[str]], tuple[int, str, str]]
MakeFile = Callable[[str, str], Path]


@pytest.fixture
def default_output(run_cli: RunCli, test_file: MakeFile) -> str:
    path = test_file(NO_ASSERTS, "test_example.py")
    return run_cli([str(path)])[1].strip()


@pytest.fixture
def default_output_parts(run_cli: RunCli, test_file: MakeFile) -> list[str]:
    path = test_file(NO_ASSERTS, "test_example.py")
    first_line = run_cli([str(path)])[1].strip().split("\n")[0]
    return first_line.split(":")
