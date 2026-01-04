"""Unit tests for the __main__ module."""

from __future__ import annotations

import importlib
from unittest.mock import patch

import pytest


@pytest.mark.unit
class TestMainModule:
    """Tests for __main__ module."""

    def test_calls_main(self) -> None:
        """Verify __main__ calls main()."""
        with patch("assert_one_assert_per_pytest.cli.main") as mock_main:
            # pylint: disable=import-outside-toplevel
            import assert_one_assert_per_pytest.__main__ as main_module

            importlib.reload(main_module)
            assert mock_main.called

    def test_main_module_exists(self) -> None:
        """Verify __main__ module can be imported."""
        # pylint: disable=import-outside-toplevel
        import assert_one_assert_per_pytest.__main__

        assert assert_one_assert_per_pytest.__main__ is not None
