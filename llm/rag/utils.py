from bs4 import BeautifulSoup
import re
from typing import List, Union, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_relevant_selectors(html_content: Union[str, List[str], List[Dict[str, Any]]]) -> str:
    """
    Extract relevant selectors from HTML content.
    Args:
        html_content: Either a single HTML string, a list of HTML strings, or a list of dictionaries containing HTML content
    Returns:
        A string containing important selectors and their context, organized by page.
    """
    # Convert input to list of HTML strings with page information
    if isinstance(html_content, str):
        logger.info("Processing single HTML string")
        html_contents = [{"html": html_content, "page": 1}]
    elif isinstance(html_content, list):
        if html_content and isinstance(html_content[0], dict):
            # Handle list of dictionaries
            logger.info("Processing list of dictionaries with HTML content")
            html_contents = []
            for i, item in enumerate(html_content, 1):
                if isinstance(item, dict) and 'html' in item:
                    html_contents.append({
                        "html": item['html'],
                        "page": i,
                        "url": item.get('url', f'Page {i}')
                    })
                    logger.info(f"Added HTML content from URL: {item.get('url', f'Page {i}')}")
        else:
            # Handle list of strings
            logger.info("Processing list of HTML strings")
            html_contents = [{"html": html, "page": i} for i, html in enumerate(html_content, 1)]
    else:
        logger.warning(f"Unexpected input type: {type(html_content)}")
        html_contents = []
    
    # Process each HTML content
    page_selectors = []
    for page_info in html_contents:
        html = page_info["html"]
        page_num = page_info["page"]
        url = page_info.get("url", f"Page {page_num}")
        
        if not html:  # Skip empty strings
            logger.warning(f"Skipping empty HTML content for {url}")
            continue
            
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Initialize sets for this page
            id_selectors = set()
            class_selectors = set()
            input_selectors = set()
            button_selectors = set()
            data_selectors = set()  # New set for data attributes
            
            # Find all elements with IDs
            id_elements = soup.find_all(id=True)
            id_selectors.update(f"#{elem['id']}" for elem in id_elements)
            logger.info(f"Found {len(id_selectors)} ID selectors on {url}")
            
            # Find all elements with data attributes
            for element in soup.find_all():
                for attr in element.attrs:
                    if attr.startswith('data-'):
                        # Create selector with the element type and data attribute
                        element_type = element.name
                        data_value = element[attr]
                        data_selectors.add(f"{element_type}[{attr}='{data_value}']")
                        
                        # Add compound selectors with class for more specificity
                        if element.has_attr('class'):
                            classes = element.get('class', [])
                            if isinstance(classes, str):
                                classes = [classes]
                            for cls in classes:
                                data_selectors.add(f"{element_type}.{cls}[{attr}='{data_value}']")
                        
                        # Add compound selectors with href for links
                        if element.name == 'a' and element.has_attr('href'):
                            href = element['href']
                            data_selectors.add(f"a[{attr}='{data_value}'][href='{href}']")
                            
                        # Add compound selectors with role
                        if element.has_attr('role'):
                            role = element['role']
                            data_selectors.add(f"{element_type}[{attr}='{data_value}'][role='{role}']")
            
            logger.info(f"Found {len(data_selectors)} data attribute selectors on {url}")
            
            # Find specific navigation elements
            nav_selectors = set()
            nav_elements = soup.find_all(['a', 'nav', 'button'])
            for elem in nav_elements:
                if elem.name == 'a' and elem.has_attr('href'):
                    href = elem['href']
                    
                    # Create specific nav selectors
                    if elem.has_attr('class'):
                        classes = elem.get('class', [])
                        if isinstance(classes, str):
                            classes = [classes]
                        for cls in classes:
                            nav_selectors.add(f"a.{cls}[href='{href}']")
                    
                    # Add more attributes for uniqueness
                    attr_pairs = []
                    for attr in elem.attrs:
                        if attr not in ['href', 'class']:
                            attr_pairs.append(f"[{attr}='{elem[attr]}']")
                    
                    if attr_pairs:
                        nav_selector = f"a[href='{href}']{attr_pairs[0]}"
                        nav_selectors.add(nav_selector)
                        
                        if len(attr_pairs) > 1:
                            nav_selector = f"a[href='{href}']{attr_pairs[0]}{attr_pairs[1]}"
                            nav_selectors.add(nav_selector)
            
            logger.info(f"Found {len(nav_selectors)} navigation selectors on {url}")
            
            # Find all elements with classes
            class_elements = soup.find_all(class_=True)
            for elem in class_elements:
                classes = elem.get('class', [])
                if isinstance(classes, str):
                    classes = [classes]
                class_selectors.update(f".{cls}" for cls in classes)
            logger.info(f"Found {len(class_selectors)} class selectors on {url}")
            
            # Find all input elements
            input_elements = soup.find_all('input')
            for elem in input_elements:
                input_type = elem.get('type', '')
                input_name = elem.get('name', '')
                input_id = elem.get('id', '')
                
                if input_id:
                    input_selectors.add(f"#{input_id}")
                if input_name:
                    input_selectors.add(f"[name='{input_name}']")
                if input_type:
                    input_selectors.add(f"input[type='{input_type}']")
            logger.info(f"Found {len(input_selectors)} input selectors on {url}")
            
            # Find all button elements
            button_elements = soup.find_all('button')
            for elem in button_elements:
                button_text = elem.get_text().strip()
                button_id = elem.get('id', '')
                button_class = elem.get('class', [])
                
                if button_id:
                    button_selectors.add(f"#{button_id}")
                if button_class:
                    if isinstance(button_class, str):
                        button_class = [button_class]
                    button_selectors.update(f".{cls}" for cls in button_class)
                if button_text:
                    button_selectors.add(f"button:has-text('{button_text}')")
            logger.info(f"Found {len(button_selectors)} button selectors on {url}")
            
            # Store selectors for this page
            page_selectors.append({
                "page": page_num,
                "url": url,
                "selectors": {
                    'IDs': sorted(list(id_selectors)),
                    'Classes': sorted(list(class_selectors)),
                    'Inputs': sorted(list(input_selectors)),
                    'Buttons': sorted(list(button_selectors)),
                    'Data Attributes': sorted(list(data_selectors)),
                    'Navigation': sorted(list(nav_selectors))
                }
            })
            
        except Exception as e:
            logger.error(f"Error processing HTML content for {url}: {str(e)}")
            continue
    
    # Format the output by page
    output = "Page Flow and Selectors:\n"
    for page_info in page_selectors:
        output += f"\nPage {page_info['page']} ({page_info['url']}):\n"
        for category, selectors in page_info['selectors'].items():
            if selectors:
                output += f"\n{category}:\n"
                output += "\n".join(f"- {selector}" for selector in selectors)
    
    logger.info("Successfully extracted all selectors")
    return output 