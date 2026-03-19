from datetime import datetime

from loguru import logger
from telegram import Update
from telegram.ext import ContextTypes

from app.checker.site_checker import check_site, ErrorType
from app.config.settings import settings
from app.notifier.telegram import send_error_notification
from app.scheduler.monitor import last_results


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "👋 <b>Site Availability Monitor</b>\n\n"
        "Я слежу за доступностью сайтов и оповещаю об ошибках.\n\n"
        "Команды:\n"
        "/status — статус всех отслеживаемых сайтов\n"
        "/check <code>&lt;url&gt;</code> — проверить сайт прямо сейчас"
    )
    await update.message.reply_text(text, parse_mode="HTML")


async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not settings.sites:
        await update.message.reply_text("Нет настроенных сайтов для мониторинга.")
        return

    lines = ["<b>Статус сайтов:</b>\n"]
    for url in settings.sites:
        result = last_results.get(url)
        if result is None:
            lines.append(f"⏳ {url} — ещё не проверялся")
        elif result.ok:
            latency = f", {result.latency_ms:.0f} мс" if result.latency_ms is not None else ""
            lines.append(f"✅ {url} — OK [{result.status}{latency}]")
        elif result.error_type == ErrorType.TIMEOUT:
            lines.append(f"⏱ {url} — Таймаут")
        else:
            status_info = f"HTTP {result.status}" if result.status else result.exc or "неизвестная ошибка"
            latency = f", {result.latency_ms:.0f} мс" if result.latency_ms is not None else ""
            lines.append(f"🔴 {url} — Ошибка ({status_info}{latency})")

    await update.message.reply_text("\n".join(lines), parse_mode="HTML")


async def check_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Укажите URL. Пример: /check https://example.com")
        return

    url = context.args[0]
    await update.message.reply_text(f"Проверяю {url}...")

    result = await check_site(url)
    last_results[url] = result

    if result.ok:
        latency = f", {result.latency_ms:.0f} мс" if result.latency_ms is not None else ""
        await update.message.reply_text(f"✅ {url} — OK [{result.status}{latency}]")
        return

    if result.error_type == ErrorType.TIMEOUT:
        await update.message.reply_text(f"⏱ {url} — Таймаут")
        return

    if result.error_type == ErrorType.HTTP_ERROR:
        msg = f"🔴 <b>Ошибка</b>\n\nURL: {url}\nHTTP статус: {result.status}\nВремя: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    else:
        msg = f"🔴 <b>Ошибка</b>\n\nURL: {url}\nОшибка: {result.exc}\nВремя: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    if result.screenshot:
        await send_error_notification(context.bot, url, msg, result.screenshot)
        await update.message.reply_text("Скриншот отправлен в чат мониторинга.")
    else:
        await update.message.reply_text(msg, parse_mode="HTML")
