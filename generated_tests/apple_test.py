from playwright.sync_api import Page, expect


def test_main(page: Page):
    page.goto("https://apple.com/ca/")  # Navigate to the initial URL

    page = step_1_click_buy_macbook_air(page)  # 1. From the home page click the "Buy" button of the macbook-air section
    page.wait_for_load_state('load')
    html = page.content()
    with open('latest_page.html', 'w', encoding='utf-8') as f:
        f.write(html)

    page = step_2_verify_macbook_air_heading(page)  # 2. Verify "Choose your new MacBook Air." appears
    page.wait_for_load_state('load')
    html = page.content()
    with open('latest_page.html', 'w', encoding='utf-8') as f:
        f.write(html)


def step_1_click_buy_macbook_air(page: Page):
    buy_button = page.get_by_role("link", name="Buy, MacBook Air with M4 chip")
    expect(buy_button).to_be_visible(timeout=10000)
    expect(buy_button).to_be_enabled()
    buy_button.click()
    return page


def step_2_verify_macbook_air_heading(page: Page):
    heading = page.get_by_role("heading", name="Choose your new MacBook Air.")
    expect(heading).to_be_visible(timeout=10000)
    return page