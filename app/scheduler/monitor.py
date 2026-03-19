from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger
from telegram import Bot

from app.checker.site_checker import check_site, ErrorType
from app.config.settings import settings
from app.notifier.telegram import send_error_notification

# Stores last check results: {url: CheckResult}
last_results: dict = {}


async def monitor_site(bot: Bot, url: str) -> None:
    result = await check_site(url)
    last_results[url] = result

    if result.error_type == ErrorType.TIMEOUT:
        return

    if not result.ok:
        if result.error_type == ErrorType.HTTP_ERROR:
            msg = f"🔴 <b>Ошибка сайта</b>\n\nURL: {url}\nHTTP статус: {result.status}\nВремя: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        else:
            msg = f"🔴 <b>Ошибка сайта</b>\n\nURL: {url}\nОшибка: {result.exc}\nВремя: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        await send_error_notification(bot, url, msg, result.screenshot)


def create_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()

    for url in settings.sites:
        scheduler.add_job(
            monitor_site,
            trigger="interval",
            seconds=settings.check_interval,
            args=[bot, url],
            id=f"monitor_{url}",
            next_run_time=datetime.now(),
        )
        logger.info(f"Scheduled monitoring for {url} every {settings.check_interval}s")

    return scheduler
