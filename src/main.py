import logging
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
    CHOOSING_ROLE,
    MESSAGES,
    ROLE_BUTTONS,
)

# Teacher Telegram ID (imported from envs)
from envs import TEACHER_TELEGRAM_ID

# Dictionary to store user states
user_states: Dict[int, Dict] = {}

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def get_role_keyboard():
    """Creates keyboard for role selection"""
    keyboard = [
        [
            InlineKeyboardButton(ROLE_BUTTONS["teacher"], callback_data="role_teacher"),
        ],
        [
            InlineKeyboardButton(ROLE_BUTTONS["student"], callback_data="role_student"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


async def role_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Role selection handler"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    role = query.data.split("_")[1]  # role_teacher -> teacher, role_student -> student

    # Save selected role
    if user_id not in user_states:
        user_states[user_id] = {}
    user_states[user_id]["role"] = role

    if role == "teacher":
        # For teacher, ask for username and show instruction
        await query.edit_message_text(MESSAGES["teacher_instruction"])
        return ConversationHandler.END
    else:
        # For student, show instruction
        await query.edit_message_text(MESSAGES["student_instruction"])
        return ConversationHandler.END


async def block_text_during_role_selection(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Block text input during role selection"""
    await update.message.reply_text(MESSAGES["block_text_selection"])
    return CHOOSING_ROLE


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
        await update.message.reply_text(MESSAGES["no_username"])
        return

    await update.message.reply_text(
        MESSAGES["welcome"], reply_markup=get_role_keyboard()
    )

    return CHOOSING_ROLE


async def learn_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the /learn command"""
    logger.info("Call the 'learn_command' handler")
    student_user_id: str = str(update.effective_user.id)
    logger.info(f"User {student_user_id} called /learn command")
    hello_word = ""

    if context.args:
        hello_word = context.args[0]  # TODO: not implemented yet
        hello_word = hello_word.strip()

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{envs.USERS_GROUPS_MCP_ENDPOINT}/get_username_by_user_id",
            json={"user_id": student_user_id},
        )

        if response.status_code == 200:
            response_data = response.json()
            logger.info(f"Response data: {response_data}")
            username = response_data["username"]
            logger.info(f"Username for the user_id '{student_user_id}': '{username}'")
            if username:
                # already have username, no need to generate
                await update.message.reply_text(MESSAGES["hello_student"].format(username=username))
                return
            else:
                response = await client.post(
                    f"{envs.USERS_GROUPS_MCP_ENDPOINT}/create_student_account",
                    json={"user_id": student_user_id},
                )
                if response.status_code == 200:
                    response_data = response.json()
                    logger.info(f"Response data: {response_data}")
                    username = response_data["username"]
                    logger.info(
                        f"Username for the user_id '{student_user_id}': '{username}'"
                    )

                    response = await client.post(
                        f"{envs.MCP_REGISTRY_ENDPOINT}/register_user",
                        json={"user_id": student_user_id, "role_name": "student"},
                    )
                    if response.status_code == 200:
                        logger.info(f"User '{student_user_id}' registered as a student")
                    else:
                        logger.error(
                            f"Error registering user '{student_user_id}' as a student: {response.status_code} {response.text}"
                        )
                        await update.message.reply_text(MESSAGES["something_wrong"])
                        return

                    await update.message.reply_text(f'{MESSAGES["your_username"]} {username}.\n\n{MESSAGES["student_actions"]}')
                    return
                else:
                    await update.message.reply_text(MESSAGES["something_wrong"])
                    return
        else:
            logger.error(
                f"Error creating student account: {response.status_code} {response.text}"
            )
            await update.message.reply_text(MESSAGES["something_wrong"])
            return


async def teach_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the /teach command"""

    logger.info("Call the 'teach_command' handler")

    if context.args:
        given_username = context.args[0]
        teacher_user_id = str(update.effective_user.id)
        logger.info(
            f"Given username='{given_username}' and teacher_user_id='{teacher_user_id}'"
        )

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
                    await update.message.reply_text(MESSAGES["username_incorrect"])
                    return
            else:
                logger.error(
                    f"Error checking username '{given_username}': {response.status_code} {response.text}"
                )
                await update.message.reply_text(MESSAGES["something_wrong"])
                return

            # Check if user_id has another username
            logger.info(f"Check if user_id '{teacher_user_id}' has another username")
            response = await client.post(
                f"{envs.USERS_GROUPS_MCP_ENDPOINT}/get_username_by_user_id",
                json={"user_id": teacher_user_id},
            )

            if response.status_code == 200:
                response_data = response.json()
                logger.info(f"Response data: {response_data}")
                username = response_data["username"]
                logger.info(
                    f"Username for the user_id '{teacher_user_id}': '{username}'"
                )

                if username and username != given_username:
                    await update.message.reply_text(MESSAGES["username_already_exists"].format(username=username))
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
                if user_id:
                    user_id = str(user_id).strip()
                    logger.info(
                        f"User_id for the username '{given_username}': '{user_id}'"
                    )

                    if user_id != teacher_user_id:
                        # it should be either empty --> new teacher registration
                        # or equal to teacher_user_id --> existing teacher
                        logger.info(
                            f"user_id either empty or not equal to teacher_user_id: "
                            f"teach_user_id={teacher_user_id}, user_id={user_id}"
                        )

                        await update.message.reply_text(MESSAGES["username_incorrect"])
                        return

                    # TODO: check that this user_id has the "teacher" role
            else:
                logger.error(
                    f"Error getting user_id for the username '{given_username}': {response.status_code} {response.text}"
                )
                await update.message.reply_text(MESSAGES["something_wrong"])
                return

            # Register new teacher into groups-users service
            if not user_id:
                # set user_id for the username
                logger.info(f"Set user_id for the username '{given_username}'")
                response = await client.post(
                    f"{envs.USERS_GROUPS_MCP_ENDPOINT}/set_user_id_for_username",
                    json={"user_id": teacher_user_id, "username": given_username},
                )
                if response.status_code != 200:
                    logger.error(
                        f"Error setting user_id for the username '{given_username}': {response.status_code} {response.text}"
                    )
                    await update.message.reply_text(MESSAGES["something_wrong"])
                    return

                # register new user into the MCP registry to allow to use tools
                logger.info(
                    "Register new user into the MCP registry to allow to use tools"
                )
                response = await client.post(
                    f"{envs.MCP_REGISTRY_ENDPOINT}/register_user",
                    json={"user_id": teacher_user_id, "role_name": "teacher"},
                )
                if response.status_code != 200:
                    logger.error(
                        f"Error registering user into the MCP registry: {response.status_code} {response.text}"
                    )
                    await update.message.reply_text(MESSAGES["something_wrong"])
                    return

            await update.message.reply_text(MESSAGES["teacher_actions"])
    else:
        await update.message.reply_text(MESSAGES["forgot_username"])
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
                await update.message.reply_text(MESSAGES["token_invalid"])
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
                    await update.message.reply_text(MESSAGES["token_invalid"])
                    return
    else:
        logger.warning(f"No parameters passed to the token command by user='{user_id}'")
        await update.message.reply_text(MESSAGES["no_parameters"])


async def check_user_is_authenticated(user_id: str) -> bool:
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Check if user allowed to speak with agent
        logger.info(f"Check if user '{user_id}' allowed to speak with agent")
        response = await client.post(
            f"{envs.USERS_GROUPS_MCP_ENDPOINT}/check_user_id_activated",
            json={"user_id": user_id},
        )

        if response.status_code == 200:
            response_data = response.json()
            logger.info(f"Response data: {response_data}")
            return response_data["activated"]
        else:
            logger.error(
                f"Status code from check_user_id_activated: {response.status_code} {response.text}"
            )
            return False


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages and process them with the agent."""
    user_id = update.effective_user.id
    message_text = update.message.text

    logger.info(f"User {user_id} sent message: {message_text}")

    is_authenticated = await check_user_is_authenticated(user_id)
    if not is_authenticated:
        await update.message.reply_text(MESSAGES["not_registered"])
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
                await update.message.reply_text(MESSAGES["message_error"])
                return
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        import traceback

        traceback.print_exc()
        error_message = MESSAGES["message_error"]
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
            CommandHandler("learn", learn_command),
        ],
        states={
            CHOOSING_ROLE: [
                CallbackQueryHandler(role_callback, pattern="^role_"),
                # Block all text messages during role selection
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    block_text_during_role_selection,
                ),
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
