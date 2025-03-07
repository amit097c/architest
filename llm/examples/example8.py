from playwright.sync_api import sync_playwright


def test_mobile_emulation():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        iphone_11 = p.devices["iPhone 11"]
        context = browser.new_context(**iphone_11)
        page = context.new_page()
        page.goto("https://example.com")
        assert page.viewport_size == {"width": 828, "height": 1792}
        browser.close()
