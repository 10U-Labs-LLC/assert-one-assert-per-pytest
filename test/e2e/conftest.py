from __future__ import annotations

from pathlib import Path
from test.helpers import run_tool

import pytest

OUTPUT_SOURCE = "\ndef test_empty():\n    pass\n"
ONE_ASSERT_SOURCE = "\ndef test_one_assert():\n    assert True\n"


@pytest.fixture
def default_output(tmp_path: Path) -> str:
    path = tmp_path / "test_output.py"
    path.write_text(OUTPUT_SOURCE)
    return run_tool(str(path)).stdout.strip()


@pytest.fixture
def verbose_output(tmp_path: Path) -> str:
    path = tmp_path / "test_example.py"
    path.write_text(ONE_ASSERT_SOURCE)
    return run_tool(str(path), "--verbose").stdout
