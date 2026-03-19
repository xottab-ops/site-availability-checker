import io
from urllib.parse import urlparse

from loguru import logger
from telegram import Bot

from app.config.settings import settings


async def send_alarm_notification(bot: Bot, url: str, message: str, screenshot: bytes | None = None, response_body: str | None = None) -> None:
    try:
        if screenshot:
            await bot.send_photo(
                chat_id=settings.alarm_chat_id,
                photo=io.BytesIO(screenshot),
                caption=message,
                parse_mode="HTML",
            )
        else:
            await bot.send_message(
                chat_id=settings.alarm_chat_id,
                text=message,
                parse_mode="HTML",
            )

        if response_body:
            domain = urlparse(url).netloc.replace(":", "_")
            filename = f"response_{domain}.txt"
            await bot.send_document(
                chat_id=settings.alarm_chat_id,
                document=io.BytesIO(response_body.encode("utf-8", errors="replace")),
                filename=filename,
                caption=f"Тело ответа для {url}",
            )

        logger.info(f"Alarm notification sent for {url}")
    except Exception as e:
        logger.error(f"Failed to send alarm notification for {url}: {e}")


async def send_recovery_notification(bot: Bot, url: str, message: str) -> None:
    try:
        await bot.send_message(
            chat_id=settings.log_chat_id,
            text=message,
            parse_mode="HTML",
        )
        logger.info(f"Recovery notification sent for {url}")
    except Exception as e:
        logger.error(f"Failed to send recovery notification for {url}: {e}")


# Обратная совместимость — перенаправляет в alarm-канал
async def send_error_notification(bot: Bot, url: str, message: str, screenshot: bytes | None = None) -> None:
    await send_alarm_notification(bot, url, message, screenshot=screenshot)
