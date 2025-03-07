from playwright.sync_api import sync_playwright


def test_take_screenshot():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("https://example.com")
        page.screenshot(path="screenshot.png")
        assert os.path.exists("screenshot.png")
        browser.close()
