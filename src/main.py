import threading

from telegram_bot_app import run_bot as run_telegram_bot
from mcp_utils.server import run_mcp_app


if __name__ == "__main__":
    telegram_bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
    mcp_thread = threading.Thread(target=run_mcp_app, daemon=True)

    telegram_bot_thread.start()
    mcp_thread.start()

    threading.Event().wait()
