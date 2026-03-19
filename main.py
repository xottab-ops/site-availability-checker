import asyncio

from loguru import logger

from app.bot.client import create_application
from app.config.settings import settings
from app.scheduler.monitor import create_scheduler
from utils.logger import setup_logger


async def main() -> None:
    setup_logger()
    logger.info("Starting Site Availability Monitor Bot")
    logger.info(f"Monitoring sites: {settings.sites}")
    logger.info(f"Check interval: {settings.check_interval}s")

    application = create_application()
    scheduler = create_scheduler(application.bot)

    scheduler.start()
    logger.info("Scheduler started")

    async with application:
        await application.start()
        await application.updater.start_polling()
        logger.info("Bot polling started")

        try:
            await asyncio.Event().wait()
        finally:
            logger.info("Shutting down...")
            scheduler.shutdown(wait=False)
            await application.updater.stop()
            await application.stop()


if __name__ == "__main__":
    asyncio.run(main())
