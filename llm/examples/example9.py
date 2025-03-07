from playwright.sync_api import sync_playwright


def test_multiple_pages():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        page1 = context.new_page()
        page2 = context.new_page()

        page1.goto("https://example.com")
        page2.goto("https://example.org")

        assert page1.title() == "Example Domain"
        assert page2.title() == "Example Domain"

        browser.close()
