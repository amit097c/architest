from playwright.sync_api import sync_playwright


def test_file_upload():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("https://example.com/upload")
        page.set_input_files("input[type='file']", "path/to/file.txt")
        page.click("button#upload")
        assert page.text_content("div#upload-result") == "File uploaded successfully"
        browser.close()
