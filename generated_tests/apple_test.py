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
    # Locate the "Buy" button in the macbook-air section using its accessible name
    buy_button = page.get_by_role("link", name="Buy, MacBook Air with M4 chip")
    expect(buy_button).to_be_visible(timeout=10000)  # Ensure the button is visible
    expect(buy_button).to_be_enabled()  # Ensure the button is enabled
    buy_button.click()  # Click the "Buy" button
    return page


def step_2_verify_macbook_air_heading(page: Page):
    # Locate the heading "Choose your new MacBook Air." using its text content
    heading = page.get_by_text("Choose your new MacBook Air.", exact=True)
    expect(heading).to_be_visible(timeout=10000)  # Ensure the heading is visible
    return page