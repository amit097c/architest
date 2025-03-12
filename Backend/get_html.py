from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, TimeoutException
import validators
import os

def get_html(url):
    if not validators.url(url):
        print("Invalid URL format. Please enter a valid URL (e.g., https://example.com).")
        return None
    
    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(15)

        try:
            driver.get(url)
            body = driver.find_element('tag name', 'body').get_attribute('outerHTML')

            os.makedirs("extracted_files", exist_ok=True)
            with open('extracted_files/scraped.html', 'w', encoding='utf-8') as file:
                file.write(body)
            driver.quit()
            print(f"Scraped HTML saved to extracted_files/scraped.html")
            return body
        
        except TimeoutException:
            print("Timeout Error: The website took too long to load (Exceeded 15 seconds).")
            return None

        finally:
            driver.quit()
    
    except WebDriverException as e:
        print(f"WebDriver Error: {e}")
        return None

    except Exception as e:
        print(f"Unexpected Error: {e}")
        return None