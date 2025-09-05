import logging
from re import U
import uuid
from typing import Dict

import envs
from storage import SessionLocal
from token_auth_db.models import AuthToken, AuthUser

import httpx
from fastmcp import Client

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ConversationHandler,
)

# Import constants from JSON file
from constants import (
    CHOOSING_LANGUAGE,
    ENTERING_NAME,
    ENTERING_SURNAME,
    LANGUAGES,
    MESSAGES,
    LANGUAGE_BUTTONS,
)

# Teacher Telegram ID (imported from envs)
from envs import TEACHER_TELEGRAM_ID

# Dictionary to store user states
user_states: Dict[int, Dict] = {}

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def get_language_keyboard():
    """Creates keyboard for language selection"""
    keyboard = [
        [
            InlineKeyboardButton(LANGUAGE_BUTTONS["ru"], callback_data="lang_ru"),
            InlineKeyboardButton(LANGUAGE_BUTTONS["en"], callback_data="lang_en"),
            InlineKeyboardButton(LANGUAGE_BUTTONS["es"], callback_data="lang_es"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Language selection handler"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    language = query.data.split("_")[1]  # lang_ru -> ru

    # Save selected language
    if user_id not in user_states:
        user_states[user_id] = {}
    user_states[user_id]["language"] = language

    if user_id == TEACHER_TELEGRAM_ID:
        # For teacher show available tools
        await query.edit_message_text(LANGUAGES[language]["teacher_tools"])
        return ConversationHandler.END
    else:
        # For student ask for name
        await query.answer()  # Answer the callback query
        await query.message.reply_text(LANGUAGES[language]["enter_name"])
        return ENTERING_NAME


async def handle_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Name input handler"""
    user_id = update.effective_user.id
    first_name = update.message.text

    if user_id not in user_states:
        await update.message.reply_text(MESSAGES["error_occurred"])
        return ConversationHandler.END

    # Validate input - only allow letters, spaces, and hyphens
    if not first_name.replace(" ", "").replace("-", "").isalpha():
        language = user_states[user_id]["language"]
        await update.message.reply_text(LANGUAGES[language]["invalid_name"])
        return ENTERING_NAME

    user_states[user_id]["first_name"] = first_name
    language = user_states[user_id]["language"]

    await update.message.reply_text(LANGUAGES[language]["enter_surname"])
    return ENTERING_SURNAME


async def handle_surname_input(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Surname input handler"""
    user_id = update.effective_user.id
    last_name = update.message.text

    if user_id not in user_states:
        await update.message.reply_text(MESSAGES["error_occurred"])
        return ConversationHandler.END

    # Validate input - only allow letters, spaces, and hyphens
    if not last_name.replace(" ", "").replace("-", "").isalpha():
        language = user_states[user_id]["language"]
        await update.message.reply_text(LANGUAGES[language]["invalid_surname"])
        return ENTERING_SURNAME

    user_states[user_id]["last_name"] = last_name
    language = user_states[user_id]["language"]

    # Get username from Telegram
    username = update.effective_user.username

    try:
        # Create user via FastMCP Client
        client = Client(f"{envs.USERS_GROUPS_MCP_ENDPOINT}/mcp")

        async with client:
            result = await client.call_tool(
                "create_user",
                {
                    "telegram_id": user_id,
                    "username": username,
                    "first_name": user_states[user_id]["first_name"],
                    "last_name": user_states[user_id]["last_name"],
                },
            )

            if "already exists" in result.data:
                # User already exists
                await update.message.reply_text(MESSAGES["user_exists"])
                logger.info(f"User {user_id} already exists in database")
            else:
                await update.message.reply_text(LANGUAGES[language]["user_created"])
                logger.info(f"User {user_id} created successfully via FastMCP Client")

    except Exception as e:
        logger.error(f"Error creating user {user_id}: {e}")
        await update.message.reply_text(LANGUAGES[language]["error"])

    # Clear user state
    if user_id in user_states:
        del user_states[user_id]

    return ConversationHandler.END


async def block_text_during_language_selection(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Block text input during language selection"""
    await update.message.reply_text(MESSAGES["block_text_selection"])
    return CHOOSING_LANGUAGE


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel registration"""
    user_id = update.effective_user.id
    if user_id in user_states:
        del user_states[user_id]

    await update.message.reply_text(MESSAGES["registration_cancelled"])
    return ConversationHandler.END


# Define command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Sends a welcome message when the /start command is issued."""
    logger.info("Call the 'start' handler")
    user_id = update.effective_user.id
    username = update.effective_user.username
    logger.info(f"User {user_id} started bot")

    # Check if username exists (required field)
    if not username:
        await update.message.reply_text(LANGUAGES["en"]["no_username"])
        return

    await update.message.reply_text(
        MESSAGES["welcome"], reply_markup=get_language_keyboard()
    )

    return CHOOSING_LANGUAGE


async def teach_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the /teach command"""

    logger.info("Call the 'teach_command' handler")

    if context.args:
        given_username = context.args[0]
        teacher_user_id = update.effective_user.id

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Check if username exists
            logger.info(f"Check if username '{given_username}' exists")
            response = await client.post(
                f"{envs.USERS_GROUPS_MCP_ENDPOINT}/check_username_exists",
                json={"username": given_username},
            )

            if response.status_code == 200:
                response_data = response.json()
                logger.info(f"Response data: {response_data}")
                if not response_data["exists"]:
                    update.message.reply_text("Hm, is your username is correct? 🤔")
                    return
            else:
                logger.error(f"Error checking username '{given_username}': {response.status_code} {response.text}")
                update.message.reply_text("Hmm, something went wrong. Contact support.")
                return

            # Get user_id for the username
            logger.info(f"Get user_id for the username '{given_username}'")
            response = await client.post(
                f"{envs.USERS_GROUPS_MCP_ENDPOINT}/get_user_id",
                json={"username": given_username},
            )
            if response.status_code == 200:
                response_data = response.json()
                logger.info(f"Response data: {response_data}")
                user_id = response_data["user_id"]
                logger.info(f"User_id for the username '{given_username}': {user_id}")

                if user_id and user_id != teacher_user_id:
                    # it should be either empty --> new teacher registration
                    # or equal to teacher_user_id --> existing teacher
                    update.message.reply_text("Hm, is your username is correct? 🤔")
                    return
            else:
                logger.error(f"Error getting user_id for the username '{given_username}': {response.status_code} {response.text}")
                update.message.reply_text("Hmm, something went wrong. Contact support.")
                return

            # Register new teacher into groups-users service
            if not user_id:
                logger.info(f"Set user_id for the username '{given_username}'")
                response = await client.post(
                    f"{envs.USERS_GROUPS_MCP_ENDPOINT}/set_user_id_for_username",
                    json={"user_id": teacher_user_id, "username": given_username},
                )
                if response.status_code != 200:
                    logger.error(f"Error setting user_id for the username '{given_username}': {response.status_code} {response.text}")
                    update.message.reply_text("Hmm, something went wrong. Contact support.")
                    return
   
                # register new user into the MCP registry to allow to use tools
                logger.info(f"Register new user into the MCP registry to allow to use tools")
                response = await client.post(
                    f"{envs.MCP_REGISTRY_ENDPOINT}/register_user",
                    json={"user_id": teacher_user_id, "role_name": "teacher"},
                )
                if response.status_code != 200:
                    logger.error(f"Error registering user into the MCP registry: {response.status_code} {response.text}")
                    update.message.reply_text("Hmm, something went wrong. Contact support.")
                    return

            await update.message.reply_text("☑️")
    else:
        update.message.reply_text("Forgot to provide your username? 🤔")
        return
 


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

    # Check if user is in registration process
    if user_id in user_states:
        await update.message.reply_text(
            "Please complete your registration first. Use /cancel to cancel registration."
        )
        return

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

    # Create ConversationHandler for registration
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("teach", teach_command),
        ],
        states={
            CHOOSING_LANGUAGE: [
                CallbackQueryHandler(language_callback, pattern="^lang_"),
                # Block all text messages during language selection
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    block_text_during_language_selection,
                ),
            ],
            ENTERING_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name_input)
            ],
            ENTERING_SURNAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_surname_input)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Add handlers
    application.add_handler(conv_handler)
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
