"""Unit tests for the __main__ module."""

from __future__ import annotations

import importlib
import sys
from unittest.mock import patch

import pytest


@pytest.mark.unit
class TestMainModule:
    """Tests for __main__ module."""

    def test_calls_main(self) -> None:
        """Verify __main__ calls main()."""
        with patch("assert_one_assert_per_pytest.cli.main") as mock_main:
            # Remove cached module if exists
            sys.modules.pop("assert_one_assert_per_pytest.__main__", None)
            # Import with main mocked
            importlib.import_module("assert_one_assert_per_pytest.__main__")
            assert mock_main.called

    def test_main_is_called_once(self) -> None:
        """Verify __main__ calls main exactly once."""
        with patch("assert_one_assert_per_pytest.cli.main") as mock_main:
            sys.modules.pop("assert_one_assert_per_pytest.__main__", None)
            importlib.import_module("assert_one_assert_per_pytest.__main__")
            mock_main.assert_called_once()
