from playwright.sync_api import sync_playwright


def test_form_submission():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("https://example.com/form")
        page.fill("input[name='name']", "John Doe")
        page.fill("input[name='email']", "john.doe@example.com")
        page.click("button[type='submit']")
        assert page.url == "https://example.com/form-success"
        browser.close()
