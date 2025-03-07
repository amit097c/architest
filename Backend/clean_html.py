from bs4 import BeautifulSoup
import tiktoken
import json
import os

def simple_clean(html):
    try:
        soup = BeautifulSoup(html, 'html.parser')
        for tag in soup.find_all(['script', 'style', 'noscript', 'style', 'path', 'link', 'iframe', 'embed', 'object', 'svg', 'g-img', 'g-menu', 'g-dialog', 'g-snackbar', 'meta']):
            tag.decompose()
        
        attributes_to_remove = ['src','href','jsname', 'jscontroller', 'ping', 'data-async-context-required', 'jsaction', 'jsdata', 'jsslot', 'data-ved', 'data-csiid', 'data-hveid', 'data-attrid', 'aria-hidden', 'aria-labelledby', 'aria-level', 'role', 'tabindex', 'onerror', 'onclick', 'onfocus', 'onblur']
        for element in soup.find_all():
            for attr in attributes_to_remove:
                if attr in element.attrs:
                    del element.attrs[attr]
        
        for tag in soup.find_all():
            if not tag.text.strip() and not tag.find():
                tag.decompose()

        return str(soup)
    except Exception as e:
        print(f"Error in simple_clean: {e}")
        return None

def hard_clean(html_content, reduction_factor=0.9):
    """Removes a portion from the end of the HTML content"""
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

def extract_important_elements(html_content):
    """Extract key elements for Playwright test generation and save them as JSON."""
    
    try:
        soup = BeautifulSoup(html_content, "html.parser")

        elements = {
            "forms": [],
            "inputs": [],
            "buttons": [],
            "links": [],
            "images": []
        }

        # Extract Forms
        for form in soup.find_all("form"):
            elements["forms"].append({
                "action": form.get("action", "N/A"),
                "method": form.get("method", "GET"),
                "id": form.get("id", "N/A"),
                "class": form.get("class", "N/A"),
                "fields": [inp.get("name", "N/A") for inp in form.find_all("input") if inp.get("name")]
            })

        # Extract Input Fields
        for inp in soup.find_all("input"):
            elements["inputs"].append({
                "name": inp.get("name", "N/A"),
                "type": inp.get("type", "text"),
                "placeholder": inp.get("placeholder", "N/A"),
                "id": inp.get("id", "N/A"),
                "class": inp.get("class", "N/A")
            })

        # Extract Buttons
        for btn in soup.find_all("button"):
            elements["buttons"].append({
                "text": btn.get_text(strip=True),
                "id": btn.get("id", "N/A"),
                "class": btn.get("class", "N/A"),
                "type": btn.get("type", "button")
            })

        # Extract Links
        for a in soup.find_all("a"):
            elements["links"].append({
                "text": a.get_text(strip=True),
                "href": a.get("href", "N/A"),
                "id": a.get("id", "N/A"),
                "class": a.get("class", "N/A")
            })

        # Extract Images
        for img in soup.find_all("img"):
            elements["images"].append({
                "src": img.get("src", "N/A"),
                "alt": img.get("alt", "N/A"),
                "id": img.get("id", "N/A"),
                "class": img.get("class", "N/A")
            })
        
        os.makedirs("extracted_files", exist_ok=True)
        with open("extracted_files/extracted_elements.json", "w", encoding="utf-8") as file:
            json.dump(elements, file, indent=4)

        print(f"Extracted elements saved to extracted_elements.json")

        return elements

    except Exception as e:
        print(f"Error in extract_important_elements: {e}")
        return None

def clean_html_for_tests(html_content):
    
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
