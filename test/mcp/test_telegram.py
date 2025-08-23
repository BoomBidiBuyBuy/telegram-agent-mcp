import pytest
from unittest.mock import patch, AsyncMock


@pytest.mark.asyncio
async def test_send_message_to_user():
    with patch("mcp.telegram.Bot") as MockBot:
        mock_bot_instance = MockBot.return_value
        mock_bot_instance.send_message = AsyncMock()

        from mcp.telegram import send_message_to_user  # import after patching
        await send_message_to_user(chat_id=123456789, message="Hello, world!")

        assert mock_bot_instance.send_message.call_count == 1
        mock_bot_instance.send_message.assert_called_once_with(chat_id=123456789, text="Hello, world!")