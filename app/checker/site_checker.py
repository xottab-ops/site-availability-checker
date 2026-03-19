import time
from dataclasses import dataclass
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
    latency_ms: float | None = None
    response_body: str | None = None


async def check_site(url: str) -> CheckResult:
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            t0 = time.monotonic()
            response = await page.goto(url, timeout=settings.page_timeout)
            latency_ms = (time.monotonic() - t0) * 1000
            status = response.status if response else None

            if status is not None and status >= settings.http_error_threshold:
                screenshot = await take_screenshot(page)
                response_body: str | None = None
                try:
                    response_body = await response.text()
                except Exception:
                    pass
                logger.error(f"HTTP {status} on {url} ({latency_ms:.0f}ms)")
                return CheckResult(
                    url=url,
                    ok=False,
                    error_type=ErrorType.HTTP_ERROR,
                    status=status,
                    screenshot=screenshot,
                    latency_ms=latency_ms,
                    response_body=response_body,
                )

            logger.info(f"OK [{status}] {url} ({latency_ms:.0f}ms)")
            return CheckResult(url=url, ok=True, status=status, latency_ms=latency_ms)

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
