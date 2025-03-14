"""
html_processor.py

This module is responsible for processing extracted HTML, extracting essential elements, 
generating selectors for automation testing, and saving the processed results in JSON format.

Key Features:
- `generate_selector()`: Extracts meaningful selectors (ID, class, name, etc.) for elements.
- `process_html()`: Filters important elements from the HTML and structures them for testing.
- `save_processed_html()`: Saves the extracted element details in a structured JSON file.

"""

import requests
from typing import Dict, List, Any
from bs4 import BeautifulSoup
import json
import logging

class HTMLProcessor:
    """
    A class for processing HTML content, extracting key elements and their attributes,
    and generating structured data for test automation.
    """

    def __init__(self, log_level=logging.INFO):
        """
        Initializes the HTMLProcessor with logging and predefined element selection rules.

        Args:
            log_level (int, optional): Logging level (default: logging.INFO)
        """

        # Configure logging
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Prioritized attributes for selector generation
        self.priority_attributes = [
            'id', 
            'class', 
            'name', 
            'data-testid', 
            'data-cy'
        ]
        
        # Elements typically important for testing
        self.essential_elements = [
            'input', 'button', 'form', 
            'select', 'textarea', 
            'a', 'div', 'span', 
            'h1', 'h2', 'p', 'nav'
        ]
    
    def generate_selector(self, element) -> Dict[str, str]:
        """
        Generates a unique CSS selector for an HTML element based on prioritized attributes.

        Args:
            element (bs4.element.Tag): The BeautifulSoup parsed element.

        Returns:
            Dict[str, str]: A dictionary containing possible selector attributes.
        """

        selector = {}
        
        try:
            # Check priority attributes
            for attr in self.priority_attributes:
                if element.get(attr):
                    if attr == 'class':
                        # Convert class list to CSS selector format
                        classes = element.get('class', [])
                        if classes:
                            selector[attr] = '.' + '.'.join(classes)
                    else:
                        selector[attr] = f'[{attr}="{element[attr]}"]'
            
            # Fallback to tag name and position if no other selectors found
            if not selector:
                # Generate a more specific selector using parent context
                parents = element.find_parents()
                if parents:
                    parent_tag = parents[0].name if parents else 'body'
                    selector['tag_path'] = f'{parent_tag} > {element.name}'
        
        except Exception as e:
            self.logger.error(f"Error generating selector: {e}")
        
        return selector
    
    def process_html(self, html_content: str) -> Dict[str, Any]:
        """
        Parses HTML content and extracts essential elements along with their attributes.

        Args:
            html_content (str): Raw HTML content.

        Returns:
            Dict[str, Any]: A dictionary containing structured element data and metadata.
        """
  
        # Processed elements storage
        processed_elements = {
            'elements': [],
            'metadata': {
                'total_elements': 0,
                'essential_elements_count': 0
            }
        }
        
        try:
            # Parse HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Iterate through elements
            for element in soup.find_all():
                # Check if element is in essential elements list
                if element.name in self.essential_elements:
                    element_info = {
                        'tag': element.name,
                        'selectors': self.generate_selector(element),
                        'text': element.get_text(strip=True)[:200],  # Truncate long text
                        'attributes': dict(element.attrs)
                    }
                    
                    processed_elements['elements'].append(element_info)
            

            processed_elements['metadata']['total_elements'] = len(soup.find_all())
            processed_elements['metadata']['essential_elements_count'] = len(processed_elements['elements'])
        
        except Exception as e:
            self.logger.error(f"Error processing HTML: {e}")
        
        return processed_elements
    
    def save_processed_html(self, processed_data: Dict[str, Any], output_file: str):
        """
        Saves the processed HTML element data to a JSON file.

        Args:
            processed_data (Dict[str, Any]): The structured HTML data.
            output_file (str): File path to save the JSON output.
        """

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(processed_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Processed HTML saved to {output_file}")
        
        except Exception as e:
            self.logger.error(f"Error saving processed HTML: {e}")
