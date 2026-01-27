from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import pytest

from er_cloudflare_account.__main__ import get_ai_input  # noqa: PLC2701
from er_cloudflare_account.app_interface_input import AppInterfaceInput


@pytest.fixture
def mock_read_input_from_file() -> Iterator[MagicMock]:
    """Patch read_input_from_file"""
    with patch("er_cloudflare_account.__main__.read_input_from_file") as m:
        yield m


def test_main_get_ai_input(
    ai_input: AppInterfaceInput,
    raw_input_data: dict,
    mock_read_input_from_file: MagicMock,
) -> None:
    """Test get_ai_input"""
    mock_read_input_from_file.return_value = raw_input_data

    main_ai_input = get_ai_input()

    assert isinstance(main_ai_input, AppInterfaceInput)
    assert main_ai_input == ai_input
