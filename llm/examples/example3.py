from playwright.sync_api import sync_playwright


def test_handle_alert():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("https://example.com/alert")
        page.click("button#trigger-alert")
        page.on("dialog", lambda dialog: dialog.accept())
        assert page.text_content("div#result") == "Alert handled"
        browser.close()
