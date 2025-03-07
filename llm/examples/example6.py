from playwright.async_api import async_playwright


async def test_async_navigation():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto("https://example.com")
        assert await page.title() == "Example Domain"
        await browser.close()
