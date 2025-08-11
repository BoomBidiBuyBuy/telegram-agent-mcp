import logging
import uuid

import envs
from storage import Storage
from user import User, Token
from agent import build_agent

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


db_session = Storage().build_session().session


# Define command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message when the /start command is issued."""
    logger.info("Call the 'start' handler")
    user_id = update.effective_user.id
    logger.info(f"User {user_id} started bot")
    await update.message.reply_text(
        "Hello! I am your LLM agent MCP bot. Send me a message!"
    )


# for debugging and testing purposes
# async def add_token_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#    token_id = context.args[0]
#    Token.create(token_id, db_session)


async def token_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """User pass an issued token to us.
    It allows to connect issued token with an user id.
    """
    user_id = update.effective_user.id
    username = update.effective_user.username

    logging.info(f"user='{user_id}' with username='{username}' tries to add a token")

    if context.args:
        passed_token = context.args[0]

        token = Token.find_by_id(passed_token, db_session)

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

            user = User.find_by_id(user_id, db_session)

            if not user:
                logger.info("New user case")
                token.user = User.create(user_id, username, db_session)
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
        # Build the agent
        agent = await build_agent()
        
        # Process the message
        result = await agent.ainvoke({"messages": [{"role": "user", "content": message_text}]})
        
        # Get the response
        response = result["messages"][-1].content if result["messages"] else "Sorry, I couldn't process your message."
        
        await update.message.reply_text(response)
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        await update.message.reply_text("Sorry, there was an error processing your message.")


def main():
    """Starts the bot."""
    application = Application.builder().token(envs.TELEGRAM_BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("token", token_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
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
            listen="0.0.0.0",
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
    main()
