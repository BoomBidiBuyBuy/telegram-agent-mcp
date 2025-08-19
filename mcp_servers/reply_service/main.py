import os
import sys

from fastmcp import FastMCP
from telegram import Bot
from telegram.error import TelegramError

# Ensure we can import from project src when running this file directly
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
SRC_PATH = os.path.join(PROJECT_ROOT, "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

import envs  # noqa: E402

mcp_server = FastMCP(name="ReplyService")


@mcp_server.tool
async def send_message_to_user(chat_id: int, message: str) -> str:
    """Send a message to a specific Telegram user.

    Parameters:
    - chat_id: Telegram chat/user id to send the message to
    - message: Text content to send
    """

    bot = Bot(token=envs.TELEGRAM_BOT_TOKEN)

    try:
        await bot.send_message(chat_id=chat_id, text=message)
    except TelegramError as exc:
        return f"Failed to send message: {exc}"

    return "Message sent successfully"


def main() -> None:
    mcp_server.run(
        transport="http",
        host=envs.REPLY_SERVICE_MCP_HOST,
        port=envs.REPLY_SERVICE_MCP_PORT,
    )

if __name__ == "__main__":
    main()