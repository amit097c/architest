"""
get_html.py

This module extracts the full HTML content of a given URL using Selenium WebDriver.
It uses headless Chrome to fetch the web page and extracts only the <body> content.

Key Features:
- Uses Selenium with Chrome WebDriver in headless mode.
- Validates URL before processing.
- Implements a timeout of 15 seconds for page loading.
- Saves extracted HTML to 'extracted_files/scraped.html'.
- Handles exceptions for invalid URLs, timeout issues, and WebDriver errors.

"""
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, TimeoutException
import validators
import os

def get_html(url):
    """
    Extracts the HTML content of the given URL's <body> tag using Selenium.

    Args:
        url (str): The URL of the web page to extract HTML from.

    Returns:
        str or None: The extracted HTML content (body tag only) if successful, otherwise None.
    """
    
    # Validate the provided URL before proceeding
    if not validators.url(url):
        print("Invalid URL format. Please enter a valid URL (e.g., https://example.com).")
        return None
    
    try:
        # Configure Chrome WebDriver options for headless browsing
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-dev-shm-usage")

        # Initialize Selenium WebDriver with the configured options
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(15)

        try:
            # Open the given URL
            driver.get(url)

            # Extract the <body> tag's outerHTML
            body = driver.find_element('tag name', 'body').get_attribute('outerHTML')

            # Ensure the output directory exists
            os.makedirs("extracted_files", exist_ok=True)

            # Save the extracted HTML to a file
            with open('extracted_files/scraped.html', 'w', encoding='utf-8') as file:
                file.write(body)

            driver.quit()

            print(f"Scraped HTML saved to extracted_files/scraped.html")
            return body
        
        except TimeoutException:
            # Handle cases where the website takes too long to load
            print("Timeout Error: The website took too long to load (Exceeded 15 seconds).")
            return None

        finally:
            driver.quit()
    
    except WebDriverException as e:
        # Handle WebDriver-related errors
        print(f"WebDriver Error: {e}")
        return None

    except Exception as e:
        # Handle any other unexpected errors
        print(f"Unexpected Error: {e}")
        return None