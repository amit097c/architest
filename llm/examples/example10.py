from playwright.sync_api import sync_playwright


def test_wait_for_element():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("https://example.com")
        page.wait_for_selector("h1")
        assert page.text_content("h1") == "Example Domain"
        browser.close()
