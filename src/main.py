import logging

import envs

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


# Define command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message when the /start command is issued."""
    logger.info("Call the 'start' handler")
    user_id = update.effective_chat.id
    logger.info(f"User {user_id} started bot")
    await update.message.reply_text(
        "Hello! I am your LLM agent MCP bot. Send me a message!"
    )


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echoes the user's message."""
    logger.info("Call the 'echo' handler")

    user_id = update.effective_chat.id
    logger.info(f"User {user_id} started bot")
    await update.message.reply_text(update.message.text)


async def token_command(update: Update, context: ContextType.DEFAULT_TYPE) -> None:
    """Provide ability to set a welcome token for users"""
    if context.args:
        user_id = update.effective_chat.id
        username = update.message.from_user.username
    else:
        update.message.reply_text(
            "No parameters passed to the command, however expected one"
        )


def main():
    """Starts the bot."""
    application = Application.builder().token(envs.TELEGRAM_BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("token", token_command, pass_args=True))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Run the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
