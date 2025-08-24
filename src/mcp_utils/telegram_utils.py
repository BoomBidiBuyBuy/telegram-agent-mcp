import logging
from typing import Annotated

from telegram import Bot
from telegram.error import TelegramError


import envs  # noqa: E402

logger = logging.getLogger(__name__)


async def send_message_to_user(
    chat_id: Annotated[int, "Telegram chat/user id to send the message to"],
    message: Annotated[str, "Text content to send"],
) -> str:
    """Send a message to a specific Telegram user."""
    logger.info(f"Sending message to user {chat_id}: {message}")
    bot = Bot(token=envs.TELEGRAM_BOT_TOKEN)

    try:
        await bot.send_message(chat_id=chat_id, text=message)
    except TelegramError as exc:
        return f"Failed to send message: {exc}"

    return "Message sent successfully"
