"""
get_html.py

This module extracts the full HTML content of a given URL using Playwright.
It uses headless Chromium to fetch the web page, handles dynamic content,
and captures elements that appear after scrolling.

Key Features:
- Uses Playwright with Chromium in headless mode
- Validates URL before processing
- Implements scrolling to capture dynamic content
- Waits for network idle to ensure content is loaded
- Saves extracted HTML to 'extracted_files/scraped.html'
- Handles exceptions for invalid URLs and browser errors
"""
from playwright.async_api import async_playwright
import validators
import os
import asyncio
import tiktoken
from clean_html import clean_html_for_tests
from bs4 import BeautifulSoup, Comment
import json
import re

# Global browser instance
_browser = None
_playwright = None

async def init_browser():
    """Initialize the global browser instance if it doesn't exist."""
    global _browser, _playwright
    if _browser is None:
        _playwright = await async_playwright().start()
        try:
            # For Windows compatibility
            _browser = await _playwright.chromium.launch(
                headless=True,
                # On Windows, we may need to handle process creation differently
                executable_path=None  # Let Playwright find the proper executable
            )
        except NotImplementedError:
            # Handle Windows-specific subprocess issue
            import sys
            if sys.platform == "win32":
                print("Windows detected. Make sure Playwright browsers are installed.")
                print("Try running: python -m playwright install chromium")
                return None
            else:
                # Re-raise for non-Windows platforms
                raise

async def close_browser():
    """Close the global browser instance."""
    global _browser, _playwright
    if _browser:
        await _browser.close()
        _browser = None
    if _playwright:
        await _playwright.stop()
        _playwright = None
         


def extract_automation_elements(html):
    """
    Extracts a simplified but complete HTML that preserves elements important for testing
    """
    soup = BeautifulSoup(html, "html.parser")
    
    # Remove only the most unnecessary elements
    for tag in soup(["script", "style"]):
        tag.decompose()
        
    # Remove comments
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()
    
    # Instead of removing elements, add special attributes to important ones
    important_tags = [
        "input", "button", "select", "option", "textarea",
        "a", "label", "form", "iframe", "table", "tr", "td",
        "div", "span", "h1", "h2", "h3", "h4", "h5", "h6", "p"
    ]
    
    # Highlight important elements with data attributes to guide the LLM
    for tag in soup.find_all(important_tags):
        tag["data-test-important"] = "true"
    
    # Save the pruned HTML
    os.makedirs("extracted_files", exist_ok=True)
    with open("extracted_files/elements.html", "w", encoding="utf-8") as f:
        f.write(str(soup))
    
    return str(soup)

def optimize_html_for_llm(html):
    """
    Optimizes HTML for LLM token consumption while preserving testable elements
    like buttons, inputs, labels, links, etc.
    """
    soup = BeautifulSoup(html, "html.parser")

    # 1. Remove script/style/meta/etc. but preserve SVGs used inside buttons/links
    for tag in soup.find_all(["script", "style", "noscript", "meta", "link"]):
        tag.decompose()
    for tag in soup.find_all("svg"):
        if not tag.find_parent(["button", "a", "label"]):
            tag.decompose()

    # 2. Remove all comments
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    # 3. Truncate large text blocks, but not inside important interactive elements
    interactive_parents = ["button", "a", "label", "option", "textarea", "input"]
    for text_node in soup.find_all(string=True):
        if (
            text_node.parent.name not in interactive_parents
            and len(text_node.strip()) > 100
        ):
            text_node.replace_with(text_node[:100] + "...")

    # 4. Keep important interactive elements and their context
    important_tags = [
        "input", "button", "select", "option", "textarea", "a", 
        "label", "form", "iframe", "table"
    ]

    # 5. Simplify deeply nested structures
    max_depth = 10

    def process_element(element, current_depth=0):
        if current_depth > max_depth:
            # Preserve the element, but remove deep children
            for child in list(element.children):
                if child.name:
                    child.decompose()
            element.append("[nested content removed]")
            return

        for child in list(element.children):
            if child.name:
                # Limit attributes on non-important tags
                if child.name not in important_tags:
                    allowed_attrs = [
                        "id", "class", "name", "type", "role",
                        "data-testid", "aria-label", "href",
                        "value", "placeholder", "title", "alt"
                    ]
                    for attr in list(child.attrs.keys()):
                        if (
                            attr not in allowed_attrs
                            and not attr.startswith("data-")
                            and not attr.startswith("aria-")
                        ):
                            del child.attrs[attr]

                    # Avoid deduplicating if it contains interactive content
                    if (
                        child.name == "div"
                        and not child.find(["button", "a", "input"])
                        and len(list(child.find_all_next(child.name, attrs=child.attrs))) > 5
                    ):
                        similar_siblings = child.find_all_next(child.name, attrs=child.attrs)
                        if len(similar_siblings) > 3:
                            for sibling in similar_siblings[3:]:
                                sibling.decompose()

                process_element(child, current_depth + 1)

    if soup.body:
        process_element(soup.body)

    # 6. Add markers for LLM guidance
    for tag in soup.find_all(important_tags):
        tag["data-test-importance"] = "high"

    # 7. Minimize whitespace
    html_str = str(soup)
    html_str = re.sub(r"\s+", " ", html_str)

    # Save optimized HTML for inspection
    os.makedirs("extracted_files", exist_ok=True)
    with open("extracted_files/optimized_for_llm.html", "w", encoding="utf-8") as f:
        f.write(html_str)

    return html_str

def clean_html(raw_html):
    """
    Minimally clean the HTML while preserving all structure important for testing
    """
    # Handle None or empty input
    if raw_html is None or not raw_html:
        print("Warning: Received empty or None HTML content")
        return "<html><body><p>No content was retrieved. Please check server logs.</p></body></html>"
    
    soup = BeautifulSoup(raw_html, "html.parser")
    
    # Remove only script and style tags
    for tag in soup(["script", "style"]):
        tag.decompose()
        
    # Clean comments
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()
    
    # Don't remove any other elements to ensure no important elements are lost
    
    return str(soup)

async def scroll_to_bottom(page):
    """
    Scrolls the page to the bottom and waits for dynamic content to load.
    Optimized version with faster scrolling and smarter waiting.
    """
    await page.evaluate("""async () => {
        await new Promise((resolve) => {
            let totalHeight = 0;
            const distance = 300; // Increased scroll distance
            const timer = setInterval(() => {
                const scrollHeight = document.body.scrollHeight;
                window.scrollBy(0, distance);
                totalHeight += distance;
                
                if(totalHeight >= scrollHeight){
                    clearInterval(timer);
                    resolve();
                }
            }, 50); // Reduced interval for faster scrolling
        });
    }""")

async def get_html_async(url):
    """
    Asynchronously extracts the HTML content of the given URL using Playwright.
    Handles dynamic content and scrolling.

    Args:
        url (str): The URL of the web page to extract HTML from.

    Returns:
        str or None: The extracted HTML content if successful, otherwise None.
    """
    if not validators.url(url):
        print("Invalid URL format. Please enter a valid URL (e.g., https://example.com).")
        return None
    
    try:
        # Ensure browser is initialized
        await init_browser()
        
        # Check if browser initialization failed
        if _browser is None:
            print("Failed to initialize browser. Make sure Playwright is properly installed.")
            print("On Windows, run: python -m playwright install chromium")
            return "<html><body><p>Error: Browser initialization failed. Please check server logs.</p></body></html>"
        
        # Create a new context with optimized settings
        context = await _browser.new_context(
            ignore_https_errors=True,
            viewport={'width': 1920, 'height': 1080},
            bypass_csp=True  # Bypass Content Security Policy for faster loading
        )
        
        try:
            # Create a new page with reduced timeout
            page = await context.new_page()
            page.set_default_timeout(15000)  # Reduced to 15 seconds
            
            # Navigate to the URL with optimized waiting strategy
            await page.goto(url, wait_until='domcontentloaded')  # Changed from networkidle
            
            # Scroll to bottom and wait for dynamic content
            await scroll_to_bottom(page)
            
            # Get the full HTML content
            content = await page.content()
            
            # Ensure the output directory exists
            os.makedirs("extracted_files", exist_ok=True)
            
            # Save the extracted HTML to a file
            with open('extracted_files/scraped.html', 'w', encoding='utf-8') as file:
                file.write(content)
            
            print(f"Scraped HTML saved to extracted_files/scraped.html")
            return content
            
        except Exception as e:
            print(f"Error during page processing: {e}")
            return None
            
        finally:
            await context.close()
            
    except Exception as e:
        print(f"Unexpected Error: {e}")
        return None

async def get_html(url):
    """
    Asynchronous function to extract HTML content.
    This version is compatible with FastAPI's event loop.

    Args:
        url (str): The URL of the web page to extract HTML from.

    Returns:
        str or None: The extracted HTML content if successful, otherwise None.
    """
    return await get_html_async(url)

def count_tokens(text, model="gpt-4"):
    """
    Returns the number of tokens for a given text and model.
    """
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))