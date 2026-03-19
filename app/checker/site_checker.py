from dataclasses import dataclass, field
from enum import Enum, auto

from loguru import logger
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

from app.checker.screenshot import take_screenshot
from app.config.settings import settings


class ErrorType(Enum):
    NONE = auto()
    TIMEOUT = auto()
    HTTP_ERROR = auto()
    EXCEPTION = auto()


@dataclass
class CheckResult:
    url: str
    ok: bool = False
    error_type: ErrorType = ErrorType.NONE
    status: int | None = None
    screenshot: bytes | None = None
    exc: str | None = None


async def check_site(url: str) -> CheckResult:
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            response = await page.goto(url, timeout=settings.page_timeout)
            status = response.status if response else None

            if status is not None and status >= settings.http_error_threshold:
                screenshot = await take_screenshot(page)
                logger.error(f"HTTP {status} on {url}")
                return CheckResult(
                    url=url,
                    ok=False,
                    error_type=ErrorType.HTTP_ERROR,
                    status=status,
                    screenshot=screenshot,
                )

            logger.info(f"OK [{status}] {url}")
            return CheckResult(url=url, ok=True, status=status)

        except PlaywrightTimeout:
            logger.warning(f"Timeout: {url}")
            return CheckResult(url=url, ok=False, error_type=ErrorType.TIMEOUT)

        except Exception as e:
            logger.error(f"Error checking {url}: {e}")
            try:
                screenshot = await take_screenshot(page)
            except Exception:
                screenshot = None
            return CheckResult(
                url=url,
                ok=False,
                error_type=ErrorType.EXCEPTION,
                screenshot=screenshot,
                exc=str(e),
            )
        finally:
            await browser.close()
