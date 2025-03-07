import requests
from typing import Dict, List, Any
from bs4 import BeautifulSoup
import json
import logging

class HTMLProcessor:
    def __init__(self, log_level=logging.INFO):

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
    
    def fetch_and_process_url(self, url: str, timeout: int = 10) -> Dict[str, Any]:
    
        try:
            # Fetch HTML content
            self.logger.info(f"Fetching HTML from URL: {url}")
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()  # Raise an exception for bad status codes
            
            # Process fetched HTML
            return self.process_html(response.text)
        
        except requests.RequestException as e:
            self.logger.error(f"Error fetching URL {url}: {e}")
            return {
                'error': str(e),
                'url': url
            }
    
    def save_processed_html(self, processed_data: Dict[str, Any], output_file: str):
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(processed_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Processed HTML saved to {output_file}")
        
        except Exception as e:
            self.logger.error(f"Error saving processed HTML: {e}")
def main():
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG, 
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Initialize processor with debug logging
    processor = HTMLProcessor(log_level=logging.DEBUG)
    
    ## Assuming HTML is stored in a file
    processor = HTMLProcessor()

# Read HTML from file
    with open('extracted_files/cleaned.html', 'r') as file:
       html_content = file.read()

# Process HTML
    processed_result = processor.process_html(html_content)

# Save processed result
    processor.save_processed_html(processed_result, 'processed_html_output.json')
        
        # Optional: Print processed elements
    print(json.dumps(processed_result, indent=2))
    
    try:
        # Read HTML from file
        with open('extracted_files/cleaned.html', 'r') as file:
            html_content = file.read()

        # Process HTML
        processed_result = processor.process_html(html_content)

        # Save processed result
        processor.save_processed_html(processed_result, 'processed_html_output.json')
        
        # Optional: Print processed elements
        print(json.dumps(processed_result, indent=2))
    
    except Exception as e:
        logging.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()