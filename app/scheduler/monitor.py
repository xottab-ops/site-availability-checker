from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger
from telegram import Bot

from app.checker.site_checker import check_site, ErrorType
from app.config.settings import settings
from app.notifier.telegram import send_alarm_notification, send_recovery_notification

# Stores last check results: {url: CheckResult}
last_results: dict = {}

# Tracks previous ok-status for recovery detection: {url: bool}
_prev_ok: dict[str, bool] = {}

# Tracks when last alarm notification was sent: {url: datetime}
_last_notified: dict[str, datetime] = {}


def _should_notify(url: str) -> bool:
    last = _last_notified.get(url)
    if last is None:
        return True
    return datetime.now() - last >= timedelta(seconds=settings.notify_interval)


async def monitor_site(bot: Bot, url: str) -> None:
    result = await check_site(url)
    prev_ok = _prev_ok.get(url)
    last_results[url] = result

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    latency_str = f"\nЗадержка: {result.latency_ms:.0f} мс" if result.latency_ms is not None else ""

    if result.ok:
        # Recovery: was failing, now ok
        if prev_ok is False:
            msg = (
                f"🟢 <b>Сайт восстановлен</b>\n\n"
                f"URL: {url}\n"
                f"HTTP статус: {result.status}"
                f"{latency_str}\n"
                f"Время: {now_str}"
            )
            await send_recovery_notification(bot, url, msg)
            _last_notified.pop(url, None)
    else:
        if result.error_type == ErrorType.HTTP_ERROR:
            msg = (
                f"🔴 <b>Ошибка сайта</b>\n\n"
                f"URL: {url}\n"
                f"HTTP статус: {result.status}"
                f"{latency_str}\n"
                f"Время: {now_str}"
            )
        elif result.error_type == ErrorType.TIMEOUT:
            msg = (
                f"⏱ <b>Таймаут</b>\n\n"
                f"URL: {url}\n"
                f"Время: {now_str}"
            )
        else:
            msg = (
                f"🔴 <b>Ошибка сайта</b>\n\n"
                f"URL: {url}\n"
                f"Ошибка: {result.exc}\n"
                f"Время: {now_str}"
            )

        if _should_notify(url):
            await send_alarm_notification(
                bot, url, msg,
                screenshot=result.screenshot,
                response_body=result.response_body,
            )
            _last_notified[url] = datetime.now()

    _prev_ok[url] = result.ok


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
