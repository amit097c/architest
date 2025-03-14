"""
clean_html.py

This module is responsible for cleaning extracted HTML by removing unnecessary tags, attributes, 
and reducing the content to fit within a specified token limit. 

Key Features:
- `simple_clean()`: Removes non-essential HTML elements and attributes.
- `hard_clean()`: Trims excessive HTML content when the token limit is exceeded.
- `clean_html_for_tests()`: Cleans and optimizes HTML for LLM-based test script generation.

"""

from bs4 import BeautifulSoup
import tiktoken
import os

def simple_clean(html):
    """
    Cleans the given HTML content by removing unnecessary tags, attributes, and empty elements.

    Args:
        html (str): The raw HTML content.

    Returns:
        str: The cleaned HTML content as a string.
    """

    try:
        soup = BeautifulSoup(html, 'html.parser')
        for tag in soup.find_all(['script', 'style', 'noscript', 'style', 'path', 'link', 'iframe', 'embed', 'object', 'svg', 'g-img', 'g-menu', 'g-dialog', 'g-snackbar', 'meta']):
            tag.decompose()
        
        attributes_to_remove = ['src','href','jsname', 'jscontroller', 'ping', 'data-async-context-required', 'jsaction', 'jsdata', 'jsslot', 'data-ved', 'data-csiid', 'data-hveid', 'data-attrid', 'aria-hidden', 'aria-labelledby', 'aria-level', 'role', 'tabindex', 'onerror', 'onclick', 'onfocus', 'onblur']
        for element in soup.find_all():
            for attr in attributes_to_remove:
                if attr in element.attrs:
                    del element.attrs[attr]
        
        # Remove empty tags (tags without text or child elements)
        for tag in soup.find_all():
            if not tag.text.strip() and not tag.find():
                tag.decompose()

        return str(soup)
    except Exception as e:
        print(f"Error in simple_clean: {e}")
        return None

def hard_clean(html_content, reduction_factor=0.9):
    """
    Reduces the HTML content by removing a portion of its elements to fit within a token limit.

    Args:
        html_content (str): The cleaned HTML content.
        reduction_factor (float): The fraction of elements to retain (default is 90%).

    Returns:
        str: The reduced HTML content.
    """

    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        elements = list(soup.descendants)

        if len(elements) == 0:
                print("No elements found after initial cleaning. Returning empty HTML.")
                return ""
        
        elements_to_keep = int(len(elements) * reduction_factor)
        
        for element in elements[elements_to_keep:]:
            if hasattr(element, 'decompose'):
                element.decompose()
        return str(soup)
    
    except Exception as e:
        print(f"Error in hard_clean: {e}")
        return None

def clean_html_for_tests(html_content):
    """
    Cleans and optimizes the HTML content for LLM-based test script generation.
    Ensures the final HTML content remains within the maximum token limit.

    Args:
        html_content (str): The extracted raw HTML content.

    Returns:
        str: The cleaned and optimized HTML content.
    """
    
    MAX_TOKENS = 28000
    try:
        encoding = tiktoken.encoding_for_model('gpt-4o-mini')

        if not html_content or not isinstance(html_content, str):
            print("Invalid HTML content provided.")
            return None

        initial_tokens = encoding.encode(html_content)
        print(f"Initial token size: {len(initial_tokens)}")

        cleaned_html = simple_clean(html_content)

        if cleaned_html is None:
            print("Cleaning failed. Returning original HTML.")
            return html_content

        cleaned_tokens = encoding.encode(cleaned_html)
        print(f"Token size after simple_clean: {len(cleaned_tokens)}")

        while len(cleaned_tokens) > MAX_TOKENS:
            cleaned_html = hard_clean(cleaned_html)
            cleaned_tokens = encoding.encode(cleaned_html)
            print(f"Token size after hard_clean: {len(cleaned_tokens)}")

        os.makedirs("extracted_files", exist_ok=True)
        with open('extracted_files/cleaned.html', 'w', encoding='utf-8') as file:
            file.write(cleaned_html)

        print(f"Cleaned HTML saved to extracted_files/cleaned.html")
        return cleaned_html
    
    except Exception as e:
        print(f"Unexpected Error in clean_html_for_tests: {e}")
        return None
