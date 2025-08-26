import logging
import uuid
from typing import Dict, Optional

import envs
from storage import SessionLocal
from token_auth_db.models import AuthToken, AuthUser

import httpx

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

# States for ConversationHandler
CHOOSING_LANGUAGE, ENTERING_NAME, ENTERING_SURNAME = range(3)

# Dictionary to store user states
user_states: Dict[int, Dict] = {}

# Teacher Telegram ID (imported from envs)
from envs import TEACHER_TELEGRAM_ID

# Languages and their messages
LANGUAGES = {
    "ru": {
        "enter_name": "Пожалуйста, введите ваше имя:",
        "enter_surname": "Пожалуйста, введите вашу фамилию:",
        "user_created": "Регистрация прошла успешна!",
        "teacher_tools": "Что ты можешь сделать:\n\n1. Создать группу, задав её название.\n2. Добавить ученика в группу по его никнейму в телеграмме.\n3. Удалить ученика из группы.\n4. Просмотреть все группы.\n5. Просмотреть всех учеников.\n\nВыберите действие:",
        "error": "Произошла ошибка. Попробуйте еще раз.",
        "no_username": "Для использования бота необходимо установить username в настройках Telegram. Пожалуйста, установите username и попробуйте снова."
    },
    "en": {
        "enter_name": "Please enter your first name:",
        "enter_surname": "Please enter your last name:",
        "user_created": "Registration completed successfully!",
        "teacher_tools": "What can you do:\n\n1. Create a group, giving it a name.\n2. Add a student to a group by their Telegram username.\n3. Remove a student from a group.\n4. View all groups.\n5. View all students.\n\nChoose an action:",
        "error": "An error occurred. Please try again.",
        "no_username": "To use the bot, you need to set a username in Telegram settings. Please set a username and try again."
    },
    "es": {
        "enter_name": "Por favor, introduce tu nombre:",
        "enter_surname": "Por favor, introduce tu apellido:",
        "user_created": "¡Registro completado exitosamente!",
        "teacher_tools": "¿Qué puedes hacer?\n\n1. Crear un grupo, dándole un nombre.\n2. Añadir un estudiante a un grupo por su nombre de usuario de Telegram.\n3. Eliminar un estudiante de un grupo.\n4. Ver todos los grupos.\n5. Ver todos los estudiantes.\n\nElige una acción:",
        "error": "Ocurrió un error. Por favor, intenta de nuevo.",
        "no_username": "Para usar el bot, necesitas establecer un nombre de usuario en la configuración de Telegram. Por favor, establece un nombre de usuario e intenta de nuevo."
    }
}

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def get_language_keyboard():
    """Creates keyboard for language selection"""
    keyboard = [
        [
            InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
            InlineKeyboardButton("🇺🇸 English", callback_data="lang_en"),
            InlineKeyboardButton("🇪🇸 Español", callback_data="lang_es"),
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
    
    # Check if user is a teacher
    is_teacher = user_id == TEACHER_TELEGRAM_ID
    
    if is_teacher:
        # For teacher show available tools
        await query.edit_message_text(LANGUAGES[language]["teacher_tools"])
        return ConversationHandler.END
    else:
        # For student ask for name
        await query.edit_message_text(LANGUAGES[language]["enter_name"])
        return ENTERING_NAME


async def handle_name_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Name input handler"""
    user_id = update.effective_user.id
    first_name = update.message.text
    
    if user_id not in user_states:
        await update.message.reply_text("An error occurred. Please start over with /start")
        return ConversationHandler.END
    
    user_states[user_id]["first_name"] = first_name
    language = user_states[user_id]["language"]
    
    await update.message.reply_text(LANGUAGES[language]["enter_surname"])
    return ENTERING_SURNAME


async def handle_surname_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Surname input handler"""
    user_id = update.effective_user.id
    last_name = update.message.text
    
    if user_id not in user_states:
        await update.message.reply_text("An error occurred. Please start over with /start")
        return ConversationHandler.END
    
    user_states[user_id]["last_name"] = last_name
    language = user_states[user_id]["language"]
    
    # Get username from Telegram
    username = update.effective_user.username
    
    try:
        # Create user via MCP server
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"http://{envs.HOST_IP}:{envs.USERS_GROUPS_MCP_PORT}/create_user"
            payload = {
                "telegram_id": user_id,
                "username": username,
                "first_name": user_states[user_id]["first_name"],
                "last_name": user_states[user_id]["last_name"],
            }
            response = await client.post(url, json=payload)

            if response.status_code == 200:
                response_data = response.json()
                await update.message.reply_text(LANGUAGES[language]["user_created"])
                logger.info(f"User {user_id} created successfully via MCP server")
            elif response.status_code == 400:
                # User already exists
                await update.message.reply_text("User already exists in the system.")
                logger.info(f"User {user_id} already exists in database")
            else:
                logger.error(f"MCP server error: {response.status_code} {response.text}")
                await update.message.reply_text(LANGUAGES[language]["error"])
        
    except Exception as e:
        logger.error(f"Error creating user {user_id}: {e}")
        await update.message.reply_text(LANGUAGES[language]["error"])
    
    # Clear user state
    if user_id in user_states:
        del user_states[user_id]
    
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel registration"""
    user_id = update.effective_user.id
    if user_id in user_states:
        del user_states[user_id]
    
    await update.message.reply_text("Registration cancelled. Use /start to begin.")
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
        await update.message.reply_text("To use the bot, you need to set a username in Telegram settings. Please set a username and try again.")
        return

    # Check if user is a teacher
    is_teacher = user_id == TEACHER_TELEGRAM_ID
    
    if is_teacher:
        welcome_message = """🇷🇺 Добро пожаловать! Пожалуйста, выберите язык общения:

🇺🇸 Welcome! Please choose your communication language:

🇪🇸 ¡Bienvenido! Por favor, elige tu idioma de comunicación:"""
    else:
        welcome_message = """🇷🇺 Добро пожаловать! Пожалуйста, выберите язык общения:

🇺🇸 Welcome! Please choose your communication language:

🇪🇸 ¡Bienvenido! Por favor, elige tu idioma de comunicación:"""
    
    await update.message.reply_text(
        welcome_message,
        reply_markup=get_language_keyboard()
    )
    
    logger.info(f"Start function completed for user {user_id}, returning CHOOSING_LANGUAGE state")
    return CHOOSING_LANGUAGE


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
                "thread_id": f"user_{user_id}",
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
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING_LANGUAGE: [CallbackQueryHandler(language_callback, pattern="^lang_")],
            ENTERING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name_input)],
            ENTERING_SURNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_surname_input)],
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
