import logging
import uuid

import envs
from storage import SessionLocal
from token_auth_db.models import AuthToken, AuthUser

import httpx

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


# Define command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message when the /start command is issued."""
    logger.info("Call the 'start' handler")
    user_id = update.effective_user.id
    logger.info(f"User {user_id} started bot")

    welcome_message = "Hello! I am your LLM agent MCP bot. Send me a message!"
    await update.message.reply_text(welcome_message)


async def token_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """User pass an issued token to us.
    It allows to connect issued token with an user id.
    """
    user_id = update.effective_user.id
    username = update.effective_user.username

    logging.info(f"user='{user_id}' with username='{username}' tries to add a token")

    if context.args:
        passed_token = context.args[0]

        with SessionLocal() as db_session:
            token = AuthToken.find_by_id(passed_token, db_session)

            if not token:
                logger.warning(
                    f"user='{user_id}' passed token='{passed_token}', and I can not find active token in storage"
                )
                await update.message.reply_text(
                    "Passed token is not valid, please check that it is correct"
                )
                return

            if not token.user:
                logger.info(
                    "token has no user: either a new user or new token not assigned to the user"
                )

                user = AuthUser.find_by_id(user_id, db_session)

                if not user:
                    logger.info("New user case")
                    token.user = AuthUser.create(user_id, username, db_session)
                else:
                    if passed_token not in {t.id for t in user.tokens}:
                        logger.info("Add token to a user tokens")
                        user.tokens.append(token)
                    else:
                        logger.info("Nothing to do, token already registered")
            else:
                logger.info("Token already has an user, try to check")

                if token.user_id == user_id:
                    logger.info("Token belongs to the same user, everything is Ok")
                else:
                    logger.warning(
                        f"Command executed by '{user_id}', however token belongs to '{token.user_id}'"
                    )
                    await update.message.reply_text(
                        "Passed token is not valid, please check that it is correct"
                    )
                    return
    else:
        logger.warning(f"No parameters passed to the token command by user='{user_id}'")
        await update.message.reply_text(
            "No parameters passed to the command, however expected one"
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages and process them with the agent."""
    user_id = update.effective_user.id
    message_text = update.message.text

    logger.info(f"User {user_id} sent message: {message_text}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"{envs.AGENT_ENDPOINT}/message"
            payload = {
                "message": message_text,
                "user_id": f"{user_id}",
            }
            response = await client.post(url, json=payload)

            if response.status_code == 200:
                response_data = response.json()
                logger.info(f"Worker response: {response_data}")
                await update.message.reply_text(response_data["message"])
            else:
                logger.error(f"Worker error: {response.status_code} {response.text}")
                await update.message.reply_text(
                    "Sorry, there was an error processing your message."
                )
                return
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        import traceback

        traceback.print_exc()
        error_message = "Sorry, there was an error processing your message."
        await update.message.reply_text(error_message)


def run_bot():
    """Starts the bot."""
    # Initialize database
    from storage import init_db, engine

    init_db(engine)
    logger.info("Database initialized successfully")

    application = Application.builder().token(envs.TELEGRAM_BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("token", token_command))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )
    # application.add_handler(CommandHandler("add_token", add_token_command))

    # Run the bot
    if envs.COMMUNICATION_MODE == "polling":
        logger.info("Using polling mechanism to get new events")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    elif envs.COMMUNICATION_MODE == "webhook":
        logger.info("Using webhook mechanism to get new events")

        ext_params = dict()
        if envs.SSL_KEY_PATH:
            ext_params["key"] = envs.SSL_KEY_PATH
        if envs.SSL_CERT_PATH:
            ext_params["cert"] = envs.SSL_CERT_PATH

        application.run_webhook(
            listen=envs.WEBHOOK_LISTEN,
            secret_token=uuid.uuid4().hex,
            port=envs.WEBHOOK_PORT,
            webhook_url=envs.WEBHOOK_URL,
            **ext_params,
        )
    else:
        raise ValueError(
            f"COMMUNICATION_MODE has unsupported value '{envs.COMMUNICATION_MODE}'"
        )


if __name__ == "__main__":
    run_bot()
