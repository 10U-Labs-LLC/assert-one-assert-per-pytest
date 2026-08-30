from __future__ import annotations

import importlib
import sys
from unittest.mock import patch

import pytest


@pytest.mark.unit
class TestMainModule:
    def test_calls_main(self) -> None:
        with patch("assert_one_assert_per_pytest.cli.main") as mock_main:
            sys.modules.pop("assert_one_assert_per_pytest.__main__", None)
            importlib.import_module("assert_one_assert_per_pytest.__main__")
            assert mock_main.called

    def test_main_is_called_once(self) -> None:
        with patch("assert_one_assert_per_pytest.cli.main") as mock_main:
            sys.modules.pop("assert_one_assert_per_pytest.__main__", None)
            importlib.import_module("assert_one_assert_per_pytest.__main__")
            assert mock_main.call_count == 1
