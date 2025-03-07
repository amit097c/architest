from playwright.sync_api import sync_playwright


def test_network_interception():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        def handle_request(route, request):
            if "example.com" in request.url:
                route.fulfill(status=200, body="Intercepted response")
            else:
                route.continue_()

        page.route("**/*", handle_request)
        page.goto("https://example.com")
        assert page.content() == "Intercepted response"
        browser.close()
