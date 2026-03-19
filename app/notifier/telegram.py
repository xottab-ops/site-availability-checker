import io

from loguru import logger
from telegram import Bot

from app.config.settings import settings


async def send_error_notification(bot: Bot, url: str, message: str, screenshot: bytes | None = None) -> None:
    try:
        if screenshot:
            await bot.send_photo(
                chat_id=settings.chat_id,
                photo=io.BytesIO(screenshot),
                caption=message,
                parse_mode="HTML",
            )
        else:
            await bot.send_message(
                chat_id=settings.chat_id,
                text=message,
                parse_mode="HTML",
            )
        logger.info(f"Notification sent for {url}")
    except Exception as e:
        logger.error(f"Failed to send notification for {url}: {e}")
