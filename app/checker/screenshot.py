from playwright.async_api import Page


async def take_screenshot(page: Page) -> bytes:
    return await page.screenshot(full_page=True)
