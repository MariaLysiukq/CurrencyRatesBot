import logging
import os

from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from .handlers import cmd_convert, cmd_help, cmd_history, cmd_rates, cmd_start, on_text_message

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Initializes and starts the Telegram bot"""
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        raise ValueError('`BOT_TOKEN` is not set.')
    application = Application.builder().token(bot_token).build()
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(CommandHandler("help", cmd_help))
    application.add_handler(CommandHandler("history", cmd_history))
    application.add_handler(CommandHandler("rates", cmd_rates))
    application.add_handler(CommandHandler("convert", cmd_convert))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text_message))
    logger.info("Bot has started successfully")
    application.run_polling()


main()
