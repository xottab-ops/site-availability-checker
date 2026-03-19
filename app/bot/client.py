from telegram.ext import Application, CommandHandler

from app.bot.handlers import start_handler, status_handler, check_handler
from app.config.settings import settings


def create_application() -> Application:
    app = Application.builder().token(settings.bot_token).build()

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("status", status_handler))
    app.add_handler(CommandHandler("check", check_handler))

    return app
