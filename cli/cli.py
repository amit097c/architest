#!/usr/bin/env python
"""
ArchiTest CLI - A command line interface for the ArchiTest application.

This CLI allows you to generate and run tests through the command line,
making it suitable for integration into CI/CD pipelines.
"""

import argparse
import asyncio
import json
import sys
import aiohttp
import time
from datetime import datetime
from typing import List

# ANSI colors for terminal output
class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

# Status indicators
class Status:
    SUCCESS = f"{Colors.GREEN}[✓]{Colors.RESET}"
    PENDING = f"{Colors.YELLOW}[…]{Colors.RESET}"
    ERROR = f"{Colors.RED}[✗]{Colors.RESET}"
    INFO = f"{Colors.BLUE}[ℹ]{Colors.RESET}"

async def generate_tests(url: str, test_steps: str, framework: str, language: str, 
                         max_retries: int, output_file: str = None):
    """Generate tests based on the provided URL and test steps."""
    start_time = time.time()
    print(f"\n{Colors.BOLD}ArchiTest CLI{Colors.RESET} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    print(f"{Status.PENDING} Sending URL and test steps to backend...")
    
    async with aiohttp.ClientSession() as session:
        # Send the URL to the backend for processing
        backend_url = "http://localhost:8001/send_test"
        payload = {
            "url": [url],
            "test_steps": test_steps,
            "framework": framework,
            "language": language,
            "max_retries": max_retries
        }
        
        try:
            async with session.post(backend_url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    print(f"{Status.ERROR} Error from backend: {error_text}")
                    return False
                
                response_data = await response.json()
                print(f"{Status.SUCCESS} Backend processed request successfully")
                
                # Check if script is in the response
                if 'script' in response_data:
                    print(f"{Status.SUCCESS} LLM generated test script successfully")
                    
                    # Save the script to file if output file is specified
                    if output_file:
                        try:
                            with open(output_file, 'w') as f:
                                if 'script' in response_data:
                                    f.write(response_data['script'])
                                else:
                                    json.dump(response_data, f, indent=2)
                            print(f"{Status.SUCCESS} Script saved to {Colors.BOLD}{output_file}{Colors.RESET}")
                        except Exception as e:
                            print(f"{Status.ERROR} Failed to save script: {str(e)}")
                    else:
                        # Print a summary of the script if not saving to file
                        print(f"\n{Status.INFO} Generated script summary:")
                        script_preview = response_data.get('script', '')[:200]
                        if script_preview:
                            print(f"{script_preview}...")
                            print(f"\nUse --output flag to save the script to a file")
                
                # Handle test execution result if available
                if 'execution_result' in response_data:
                    result = response_data['execution_result']
                    if result.get('success', False):
                        print(f"{Status.SUCCESS} Tests passed {Colors.GREEN}🎉{Colors.RESET}")
                    else:
                        print(f"{Status.ERROR} Tests failed: {result.get('message', 'Unknown error')}")
                
                elapsed_time = time.time() - start_time
                print(f"\n{Status.INFO} Test generation completed in {elapsed_time:.2f} seconds\n")
                return True
                
        except aiohttp.ClientError as e:
            print(f"{Status.ERROR} Error connecting to backend: {e}")
            return False

def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="ArchiTest CLI for test generation and execution")
    
    # Required arguments
    parser.add_argument("--url", required=True, help="URL to generate tests for")
    
    # Optional arguments
    parser.add_argument("--test-steps", default="", help="Test steps description or path to file containing test steps")
    parser.add_argument("--framework", default="playwright", choices=["playwright", "selenium"], 
                        help="Testing framework to use")
    parser.add_argument("--language", default="python", choices=["python", "javascript", "java"], 
                        help="Programming language for the generated tests")
    parser.add_argument("--max-retries", type=int, default=3, 
                        help="Maximum number of test retries")
    parser.add_argument("--output", help="Output file to save the generated tests")
    
    args = parser.parse_args()
    
    # If test_steps is a file path, read content from file
    test_steps = args.test_steps
    if test_steps and (test_steps.endswith('.txt') or test_steps.endswith('.md')):
        try:
            with open(test_steps, 'r') as f:
                test_steps = f.read()
            print(f"{Status.SUCCESS} Loaded test steps from {test_steps}")
        except FileNotFoundError:
            print(f"{Status.ERROR} Test steps file '{test_steps}' not found.")
            sys.exit(1)
    
    # Run the test generation
    asyncio.run(generate_tests(
        url=args.url,
        test_steps=test_steps,
        framework=args.framework,
        language=args.language,
        max_retries=args.max_retries,
        output_file=args.output
    ))

if __name__ == "__main__":
    main() 