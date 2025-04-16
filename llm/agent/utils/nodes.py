import ast
import tempfile
import subprocess
import os
from agent.utils.tools import clean_script_response
from langgraph.types import StreamWriter
import platform
import re
import shutil
from rag import rag_manager
import json
from typing import List, Dict, Any
import asyncio
from playwright.async_api import async_playwright
from langgraph.graph import END
from agent.utils.get_html import clean_html, extract_automation_elements, optimize_html_for_llm
from agent.utils.jira import add_comment_to_jira, move_ticket_to_next_status, create_bug_ticket_for_failed_test

# Optional caching setup if available
try:
    from langchain_core.cache import BaseCache, DISKCACHE_ENABLED, DISKCACHE
    HAS_CACHE = DISKCACHE_ENABLED
except ImportError:
    HAS_CACHE = False
    # Define empty class to prevent import errors if someone tries to import it
    class BaseCache:
        pass

__all__ = [
    'initialize_step_execution', 'process_current_step', 'execute_step_script',
    'retry_step', 'invoke_llm', 'execute_playwright_script',
    'execute_selenium_script', 'execute_playwright_js_script', 'handle_errors',
    'handle_framework', 'retry_with_errors', 'limit_error', 'clear_memory',
    'HAS_CACHE', 'preprocess_html_for_selectors'
]

class PlaywrightTestStep:
    def __init__(self, func_str: str, description: str):
        self.func_str = func_str
        self.name = self.extract_function_name(func_str)  # Extract function name from the string
        self.description = description

    def extract_function_name(self, code_string: str):
        try:
            tree = ast.parse(code_string)  # Parse the code string into an AST
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    return node.name
        except SyntaxError as e:
            print(f"Syntax error in code string: {e}")
        return None

    def render_test_call(self):
        return (
            f"    page = {self.name}(page)  # {self.description}\n"
            f"    page.wait_for_load_state('load')\n"
            f"    html = page.content()\n"
            f"    with open('latest_page.html', 'w', encoding='utf-8') as f:\n"
            f"        f.write(html)\n"
        )

    def render_function(self):
        """Return the function code as a string."""
        return self.func_str  # Return the function code (as provided in the string)
    

class ScriptBuilder:
    def __init__(self, base_url: str = None):
        self.steps: list[PlaywrightTestStep] = []
        self.base_url = base_url
        
    def set_url(self, new_url: str):
        self.base_url = new_url

    def add_step(self, step: PlaywrightTestStep):
        self.steps.append(step)

    def replace_last_step(self, step: PlaywrightTestStep):
        if not self.steps:
            raise IndexError("No steps to replace.")
        self.steps[-1] = step

    def render_script(self) -> str:
        if not self.base_url:
            raise ValueError("Base URL must be set before rendering the script.")
        
        imports = "from playwright.sync_api import Page, expect\n\n\n"
        test_fn = "def test_main(page: Page):\n"
        test_fn += f"    page.goto(\"{self.base_url}\")  # Navigate to the initial URL\n\n"

        for step in self.steps:
            test_fn += step.render_test_call() + "\n"

        step_fns = "\n\n\n".join(step.render_function() for step in self.steps)
        return imports + test_fn + "\n" + step_fns
    
    def reset(self):
        self.steps = []
        self.base_url = None

script_builder = ScriptBuilder()

# New function to preprocess HTML and extract unique selectors
async def preprocess_html_for_selectors(html_content, url: str = "about:blank") -> List[Dict[str, Any]]:
    """
    Preprocess HTML to extract unique and stable selectors for visible text elements.
    
    Args:
        html_content: Either a string containing HTML content, or a list of dictionaries with 'url' and 'html' keys
        url: The URL to use for the page (defaults to about:blank)
        
    Returns:
        A list of dictionaries containing text and their selectors with uniqueness information
    """
    selector_data = []
    
    # Handle the case where html_content is a list of dictionaries
    if isinstance(html_content, list) and len(html_content) > 0 and isinstance(html_content[0], dict):
        # Find the entry for the given URL, or use the first one if not found
        html_entry = next((item for item in html_content if 'url' in item and item['url'] == url), None)
        if html_entry is None:
            html_entry = html_content[0]
        
        # Extract the actual HTML content
        if 'html' in html_entry and isinstance(html_entry['html'], str):
            html_to_process = html_entry['html']
        else:
            print("Warning: Could not find valid HTML content in the list")
            return selector_data
    else:
        # Treat html_content as a string
        html_to_process = html_content if isinstance(html_content, str) else ""
    
    # If we didn't get valid HTML content, return empty result
    if not html_to_process:
        print("Warning: Empty HTML content provided")
        return selector_data
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Load the HTML content
            await page.set_content(html_to_process, wait_until="networkidle")
            
            # Get all visible text elements
            visible_texts = await page.evaluate("""() => {
                const textWalker = document.createTreeWalker(
                    document.body,
                    NodeFilter.SHOW_TEXT,
                    {
                        acceptNode: function(node) {
                            // Skip hidden elements or whitespace-only text
                            if (node.parentElement && 
                                window.getComputedStyle(node.parentElement).display !== 'none' &&
                                window.getComputedStyle(node.parentElement).visibility !== 'hidden' &&
                                node.textContent.trim() !== '') {
                                return NodeFilter.FILTER_ACCEPT;
                            }
                            return NodeFilter.FILTER_REJECT;
                        }
                    }
                );
                
                const texts = [];
                let currentNode;
                while (currentNode = textWalker.nextNode()) {
                    const text = currentNode.textContent.trim();
                    if (text && text.length > 1) { // Ignore single characters
                        texts.push(text);
                    }
                }
                
                // Filter duplicates
                return [...new Set(texts)];
            }""")
            
            # For each visible text, generate multiple selector types and check uniqueness
            for text in visible_texts:
                selectors = []
                
                # 1. Try text-based selector
                text_selector = f"text={text}"
                count_text = await page.evaluate(f"""(selector) => {{
                    return document.evaluate("count(//*[contains(text(), '{text.replace("'", "\\'")}')])", document, null, XPathResult.NUMBER_TYPE, null).numberValue;
                }}""", text_selector)
                
                selectors.append({
                    "type": "text",
                    "selector": text_selector,
                    "unique": count_text == 1
                })
                
                # 2. Try link selector for anchor tags
                if await page.evaluate(f"""() => {{
                    const elements = Array.from(document.querySelectorAll('a'));
                    return elements.some(el => el.textContent.trim() === '{text.replace("'", "\\'")}');
                }}"""):
                    href_value = await page.evaluate(f"""() => {{
                        const elements = Array.from(document.querySelectorAll('a'));
                        const el = elements.find(el => el.textContent.trim() === '{text.replace("'", "\\'")}');
                        return el ? el.getAttribute('href') : null;
                    }}""")
                    
                    if href_value:
                        href_selector = f"a[href='{href_value}']"
                        count_href = await page.locator(href_selector).count()
                        
                        selectors.append({
                            "type": "css",
                            "selector": href_selector,
                            "unique": count_href == 1
                        })
                
                # 3. Try data-testid or other common attribute selectors
                element_attrs = await page.evaluate(f"""() => {{
                    const xpath = "//*[contains(text(), '{text.replace("'", "\\'")}')]";
                    const elements = document.evaluate(xpath, document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                    const results = [];
                    
                    for (let i = 0; i < elements.snapshotLength; i++) {{
                        const el = elements.snapshotItem(i);
                        if (el.nodeType === 1) {{ // Element node
                            const attrs = {{}};
                            for (const attr of ['id', 'data-testid', 'data-test-id', 'data-cy', 'data-test', 'name', 'class']) {{
                                if (el.hasAttribute(attr)) {{
                                    attrs[attr] = el.getAttribute(attr);
                                }}
                            }}
                            if (Object.keys(attrs).length > 0) {{
                                results.push(attrs);
                            }}
                        }}
                    }}
                    return results;
                }}""")
                
                for attrs in element_attrs:
                    for attr_name, attr_value in attrs.items():
                        if attr_value:
                            css_selector = f"[{attr_name}='{attr_value}']"
                            count = await page.locator(css_selector).count()
                            
                            selectors.append({
                                "type": "css",
                                "selector": css_selector,
                                "unique": count == 1
                            })
                
                # 4. Try XPath with more context (parent elements)
                xpath_selector = await page.evaluate(f"""() => {{
                    const elements = Array.from(document.querySelectorAll('*'));
                    const exactTextEl = elements.find(el => el.textContent.trim() === '{text.replace("'", "\\'")}');
                    
                    if (!exactTextEl) return null;
                    
                    // Build XPath with parent context for more stability
                    let currentEl = exactTextEl;
                    let xpath = '';
                    const maxParentLevels = 2;
                    let parentLevel = 0;
                    
                    while (currentEl && currentEl !== document.body && parentLevel < maxParentLevels) {{
                        const tag = currentEl.tagName.toLowerCase();
                        const siblings = Array.from(currentEl.parentNode.children).filter(c => c.tagName === currentEl.tagName);
                        
                        if (siblings.length > 1) {{
                            const index = siblings.indexOf(currentEl) + 1;
                            xpath = `/${{tag}}[${{index}}]${{xpath}}`;
                        }} else {{
                            xpath = `/${{tag}}${{xpath}}`;
                        }}
                        
                        currentEl = currentEl.parentNode;
                        parentLevel++;
                    }}
                    
                    return `//body${{xpath}}[contains(text(), '{text.replace("'", "\\'")}')]`;
                }}""")
                
                if xpath_selector:
                    count_xpath = await page.evaluate(f"""(selector) => {{
                        return document.evaluate("count({xpath_selector})", document, null, XPathResult.NUMBER_TYPE, null).numberValue;
                    }}""", xpath_selector)
                    
                    selectors.append({
                        "type": "xpath",
                        "selector": xpath_selector,
                        "unique": count_xpath == 1
                    })
                
                # Add this text and its selectors to our result
                if selectors:
                    # Sort selectors by uniqueness and then by type preference (css > text > xpath)
                    sorted_selectors = sorted(
                        selectors,
                        key=lambda s: (
                            not s["unique"],  # Unique first
                            0 if s["type"] == "css" else 1 if s["type"] == "text" else 2  # css > text > xpath
                        )
                    )
                    
                    selector_data.append({
                        "text": text,
                        "selectors": sorted_selectors
                    })
        
        await browser.close()
    except Exception as e:
        print(f"Error preprocessing HTML for selectors: {str(e)}")
    
    return selector_data

# Function to initialize the step-by-step test execution
def initialize_step_execution(state, writer: StreamWriter):
    writer({"type": "info", "message": "Initializing step-by-step test execution"})
    
    # Parse the test steps string into a list of individual steps
    steps_list = [step.strip() for step in state["test_steps"].strip().split('\n') if step.strip()]
    
    # Set the base URL for the script builder
    script_builder.set_url(state["url"])
    
    # Initialize state for step-by-step execution
    updated_state = {
        "current_step_index": 0,
        "steps_list": steps_list,
        "current_step": steps_list[0] if steps_list else None,
        "completed_steps": [],
        "accumulated_script": "",
        "generated_selectors": {},
        "api_results": {},
    }
    
    # Update the state with the new values
    return {**state, **updated_state}

# Function to process the current test step
def process_current_step(state, llm, prompt_template_step, writer: StreamWriter):
    writer({"type": "info", "message": f"Processing step {state['current_step_index'] + 1}/{len(state['steps_list'])}: {state['current_step']}"})
    
    # Determine if this is the first step
    is_first_step = state["current_step_index"] == 0
    
    # Create context from previous steps
    previous_steps_context = ""
    if state["completed_steps"]:
        previous_steps_context = "Previous completed steps:\n"
        for i, step in enumerate(state["completed_steps"]):
            previous_steps_context += f"{i+1}. {step}\n"
    
    # Create context from generated selectors
    selectors_context = ""
    if state["generated_selectors"]:
        selectors_context = "Previously generated selectors:\n"
        for element, selector in state["generated_selectors"].items():
            selectors_context += f"- {element}: {selector}\n"
    
    # Create context from API results if any
    api_context = ""
    if state["api_results"]:
        api_context = "API results from previous steps:\n"
        api_context += json.dumps(state["api_results"], indent=2)
    
    script_context = state["accumulated_script"] if state["accumulated_script"] else ""
    
    # Process HTML to extract unique selectors if this is the first step and HTML content is available
    html_content = state["html_content"]
    selector_data = []
    
    if is_first_step and html_content:
        try:
            selector_data = asyncio.run(preprocess_html_for_selectors(html_content, state["url"]))
            
            # Add selector information to the state for future steps
            if selector_data:
                # Create a simplified mapping for the generated_selectors
                for item in selector_data:
                    text = item["text"]
                    # Get the most unique selector (first in the sorted list)
                    best_selector = item["selectors"][0]["selector"] if item["selectors"] else None
                    if best_selector:
                        state["generated_selectors"][text] = best_selector
        except Exception as e:
            writer({"type": "warning", "message": f"Error preprocessing HTML for selectors: {str(e)}"})
            print(f"Error preprocessing HTML for selectors: {str(e)}")
    
    selector_recommendations = ""
    
    if selector_data:
        selector_recommendations = "Recommended selectors for visible text elements:\n"
        for item in selector_data:
            text = item["text"]
            unique_selectors = [s for s in item["selectors"] if s["unique"]]
            
            if unique_selectors:
                best_selector = unique_selectors[0]
                selector_recommendations += f"- For text '{text}', use this unique selector: {best_selector['selector']} (type: {best_selector['type']})\n"
            elif item["selectors"]:
                best_selector = item["selectors"][0]
                selector_recommendations += f"- For text '{text}', use this selector (not unique): {best_selector['selector']} (type: {best_selector['type']})\n"
    print(f"selector_recommendations: {selector_recommendations}")
    
    prompt_vars = {
        "current_step": state["current_step"],
        "previous_steps_context": previous_steps_context,
        "selectors_context": selectors_context + "\n" + selector_recommendations,
        "api_context": api_context,
        "script_context": script_context,
        "url": state["url"],
        "messages": state["messages"],
        "html_content": state["html_content"]
    }
    
    base_prompt = prompt_template_step.invoke(prompt_vars)
    
    # enhanced_prompt = rag_manager.enhance_prompt(
    #     framework=state["framework"],
    #     test_steps=state["current_step"],
    #     html_content=state["html_content"],
    #     base_prompt=base_prompt
    # )
    
    response = llm.invoke(base_prompt)
    cleaned_content = clean_script_response(response.content)
    
    test_step = PlaywrightTestStep(cleaned_content, state["current_step"])
    script_builder.add_step(test_step)
    
    return {
        "messages": [{"role": "assistant", "content": cleaned_content}],
        "max_retries": state["max_retries"],
        "last_script": cleaned_content,
    }

# Function to execute the current step script
def execute_step_script(state, writer: StreamWriter):
    script_content = state["messages"][-1].content
    writer({"type": "info", "message": f"Executing step {state['current_step_index'] + 1}: {state['current_step']}"})
    print(f"script_content: {script_content}")
    
    step_script = script_builder.render_script()
    
    print(f"step_script: {step_script}")
    # Write the script to a temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(step_script)
        temp_path = f.name
    
    # Execute the script
    try:
        # Run the script with pytest
        result = subprocess.run(
            ["pytest", temp_path, "-v"],
            capture_output=True,
            text=True,
            check=False
        )
        
        # Check if the script executed successfully
        if result.returncode == 0:
            writer({"type": "success", "message": f"Step {state['current_step_index'] + 1} executed successfully"})
            writer({"type": "script", "message": step_script})
            # rag_manager.store_test_result(
            #     framework="playwright",
            #     test_script=step_script,
            #     test_steps=state["current_step"],  # Store just the current step description
            #     html_content=state["html_content"],
            #     success=True,
            #     metadata={
            #         "is_complete_script": False,
            #         "step_number": state["current_step_index"] + 1,
            #         "total_steps": len(state["steps_list"]),
            #         "step_description": state["current_step"]
            #     }
            # )

            with open('latest_page.html', 'r', encoding='utf-8') as f:
                html = f.read()
                
                if html:
                    latest_html = clean_html(html)
                    latest_html = extract_automation_elements(latest_html)
                    latest_html = optimize_html_for_llm(latest_html)
                    
                    with open('latest_html_output.html', 'w', encoding='utf-8') as html_file:
                        html_file.write(latest_html)

            # If this was the last step, send Jira success message and move ticket
            if state["current_step_index"] + 1 == len(state["steps_list"]):
                jira_id = state.get("jira_ticket_id")
                if isinstance(jira_id, str) and "SCRUM-" in jira_id:
                    try:
                        add_comment_to_jira(state["jira_ticket_id"], "✅ Test script passed successfully via ArchiTest.", state["jira_email"], state["jira_token"], state["jira_domain"])
                        move_ticket_to_next_status(state["jira_ticket_id"], state["jira_email"], state["jira_token"], state["jira_domain"])
                    except Exception as e:
                        print(f"Jira update failed: {str(e)}")
                        
            return {
                "html_content": latest_html,
                "has_errors": False,
                "error_message": None,
                "completed_steps": state["completed_steps"] + [state["current_step"]],
                "current_step_index": state["current_step_index"] + 1,
                "current_step": state["steps_list"][state["current_step_index"] + 1] if state["current_step_index"] + 1 < len(state["steps_list"]) else None,
                "accumulated_script": step_script,
            }
        else:
            # rag_manager.store_test_result(
            #     framework="playwright",
            #     test_script=step_script,
            #     test_steps=state["current_step"],  # Store just the current step description
            #     html_content=state["html_content"],
            #     success=False,
            #     error_message=error_message,
            #     metadata={
            #         "is_complete_script": False,
            #         "step_number": state["current_step_index"] + 1,
            #         "total_steps": len(state["steps_list"]),
            #         "step_description": state["current_step"]
            #     }
            # )
            error_message = result.stderr if result.stderr else result.stdout
            writer({"type": "error", "message": f"Step {state['current_step_index'] + 1} failed", "errors": error_message})
            writer({"type": "script", "message": step_script})
            
            
            return {
                # "retry_count": state.get("retry_count", 0),
                "has_errors": True,
                "error_message": error_message,
            }

    except Exception as e:
        writer({"type": "error", "message": f"Error executing step {state['current_step_index'] + 1}: {str(e)}"})
        return state
    finally:
        # Clean up the temporary file
        try:
            os.unlink(temp_path)
        except:
            pass

def retry_step(state, llm, error_prompt_step, writer: StreamWriter):
    """Retry the current failed step with error information."""

    state["retry_count"] = state.get("retry_count", 0) + 1
    max_retries = state["max_retries"]
    current_step_index = state["current_step_index"]

    writer({"type": "info", "message": f"Refining step {current_step_index + 1} (Attempt {state['retry_count']}/{max_retries})"})
    print("Retry count:", state["retry_count"], "/", max_retries)

    if state["retry_count"] >= max_retries:
        writer({
            "type": "error",
            "message": "Max refinement attempts reached. Please check your test steps and/or the webpage.",
            "details": state.get("error_message", "Unknown error")
        })

        print("\nMax retries reached. Stopping further refinements.")

        if "SCRUM-" in state.get("jira_ticket_id", ""):
                try:
                    add_comment_to_jira(state["jira_ticket_id"], "❌ Test script failed. Creating bug report...", state["jira_email"], state["jira_token"], state["jira_domain"])
                    create_bug_ticket_for_failed_test(state["jira_ticket_id"], state.get("error_message", "No details available"), state["jira_email"], state["jira_token"], state["jira_domain"])
                except Exception as e:
                    print(f"Jira bug creation failed: {e}")

        return {
            **state,
            "messages": [{"role": "system", "content": "Test generation failed. Max retries reached."}],
            "stop_execution": True,
            "error_message": "Max retries reached",
        }
    
    else:
        # Get the original script and error
        current_step_function = state["last_script"]
        error_message = state["error_message"]
        accumulated_script = state["accumulated_script"]

        # Prepare the prompt for retry
        retry_prompt = error_prompt_step.invoke({
            "original_script": current_step_function,  # Send only the current step function
            "error_message": error_message,
            "current_step": state["current_step"],
            "script_context": accumulated_script,
            "selectors_context": json.dumps(state["generated_selectors"], indent=2),
            "url": state["url"],
            "html_content": state["html_content"],
            "messages": state["messages"]
        })
        
        # Invoke LLM for correction
        response = llm.invoke(retry_prompt)
        cleaned_content = clean_script_response(response.content)
        print(f"cleaned_content: {cleaned_content}")
        test_step = PlaywrightTestStep(cleaned_content, state["current_step"])
        script_builder.replace_last_step(test_step)
        
        # Update state
        return {
            "messages": [{"role": "assistant", "content": cleaned_content}],
            "retry_count": state["retry_count"],
            "last_script": cleaned_content,
        }

def limit(state):
    return "stop" if state.get("stop_execution", False) else "retry"


# Function defined to invoke the LLM model with its configuration
def invoke_llm(state, llm, prompt_template_playwright, prompt_template_selenium, prompt_template_playwright_js, writer: StreamWriter):
    writer({"type": "info", "message": "Generating script"})
    
    framework = state["framework"]
    language = state["language"]
    
    # Get base prompt template
    if framework == "playwright":
        base_prompt = prompt_template_playwright.invoke({
            "test_steps": state["test_steps"],
            "html_content": state["html_content"],
            "url": state["url"],
            "messages": state["messages"],
        })
    else:  # selenium
        base_prompt = prompt_template_selenium.invoke({
            "test_steps": state["test_steps"],
            "html_content": state["html_content"],
            "url": state["url"],
            "messages": state["messages"],
        })
    
    # Enhance prompt with RAG context
    enhanced_prompt = rag_manager.enhance_prompt(
        framework=framework,
        test_steps=state["test_steps"],
        html_content=state["html_content"],
        base_prompt=base_prompt
    )
    
    response = llm.invoke(enhanced_prompt)
    cleaned_content = clean_script_response(response.content)
    print(f"generated {framework} {language} script: {cleaned_content}")
    
    return {"messages": [{"role": "assistant", "content": cleaned_content}],
            "max_retries": state["max_retries"],
    }

# Function defined to execute the Playwright script
def execute_playwright_script(state, writer: StreamWriter):
    # Get the last message from the state
    print("inside execute_playwright_script")
    
    # For the structured approach, we should use the accumulated script
    if "accumulated_script" in state and state["accumulated_script"]:
        script_content = state["accumulated_script"]
    else:
        # Fall back to the last message content if needed
        script_content = state["messages"][-1].content
    
    state["last_script"] = script_content
    print("\n=== Generated Script ===")
    print(script_content)
    print("=====================\n")

    # Write the script to a temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(script_content)
        temp_path = f.name

    try:
        writer({"type": "info", "message": "Executing test script"})
        
        # Run the script with shell=True to ensure proper execution
        process = subprocess.run(
            f"pytest {temp_path}", 
            shell=True,
            capture_output=True,
            text=True,
            env=os.environ.copy()  # Pass current environment
        )
        
        # Check if the process returned an error
        if process.returncode != 0:
            # Get the error output from the process
            error_output = process.stderr if process.stderr else process.stdout
            
            # Send the error message to the frontend
            writer({"type": "error", "message": "Test execution failed", "errors": error_output})
            writer({"type": "script", "message": state["last_script"]})
            
            print("\n=== Execution Error ===")
            print(error_output)
            print("=====================\n")
            
            # Store failed test in vector store
            rag_manager.store_test_result(
                framework="playwright",
                test_script=script_content,
                test_steps=state["test_steps"],
                html_content=state["html_content"],
                success=False,
                error_message=error_output
            )
            
            state["messages"].append(
                {
                    "role": "system",
                    "content": f"Script execution failed with error: {error_output}",
                }
            )
            state["has_errors"] = True
            state["error_message"] = error_output
        else:
            # Send the success message to the frontend
            writer({"type": "success", "message": "Tests executed successfully"})
            # Send the script content to the frontend
            writer({"type": "script", "message": state["last_script"]})
            print("\n=== Success ===")
            print("Script executed without errors")
            print("=============\n")
            
            # Store successful test in vector store
            rag_manager.store_test_result(
                framework="playwright",
                test_script=script_content,
                test_steps=state["test_steps"],
                html_content=state["html_content"],
                success=True
            )
            
            state["messages"].append(
                {"role": "system", "content": "Script executed successfully"}
            )
            
            # For executing the script in chrome for Chrome test stability check
            stability_check, stability_message = execute_chrome_script(state["last_script"])
            state["messages"].append({"role": "system", "content": stability_message})
            state["stability_check_passed"] = stability_check
            state["has_errors"] = False
                    
    finally:
        # Remove the temporary file after it finish everything
        os.unlink(temp_path)
    return state

# Function defined to execute the Playwright script in Chrome for chrome stability check
def execute_chrome_script(script_content):
    """Executes the given Playwright script in Chrome with headless mode off."""
    # Modify the script content to run in Chrome with headless mode off
    modified_script_content = script_content.replace(
        "(headless=True)", '(headless=True, channel="chrome")'
    ).replace(
        "(headless=False)", '(headless=True, channel="chrome")'
    )

    # Write the modified script to a temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as chrome_f:
        chrome_f.write(modified_script_content)
        chrome_temp_path = chrome_f.name
    
    try:
        print("Running Playwright test in Chrome for stability check (Headless=False)...")
        # Run the script with shell=True to ensure proper execution
        chrome_process = subprocess.run(["python", "-m", "pytest", chrome_temp_path], capture_output=True, text=True)

        # Check if the process returned an error
        if chrome_process.returncode != 0:
            print("Chrome Stability Test Failed, Test is unstable due to :\n%s", chrome_process.stderr)
            return False, chrome_process.stderr
        else:
            # If the process returned successfully
            print("Chrome Execution Passed! Test is stable.")
            return True, "Chrome execution passed."
    finally:
        # Remove the temporary file after it finish everything
        os.unlink(chrome_temp_path)


def execute_selenium_script(state, writer: StreamWriter):
    # Get the last message from the state
    print("inside execute_selenium_script")
    script_content = state["messages"][-1].content
    state["last_script"] = script_content
    print("\n=== Generated Script (JAVA) ===")
    print(script_content)
    print("=====================\n")

    match = re.search(r'public\s+class\s+(\w+)', script_content)
    if not match:
        writer({"type": "error", "message": "Could not find a public class in the script."})
        return
    class_name = match.group(1)

    with tempfile.TemporaryDirectory() as tmpdir:
        java_file_path = os.path.join(tmpdir, f"{class_name}.java")
        with open(java_file_path, "w") as f:
            f.write(script_content)

    # try:
        writer({"type": "info", "message": "Executing test script"})
        
        # Get the current script's directory (i.e., utils/)
        SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

        # Define the relative path to java_utils/
        JAVA_UTILS_DIR = os.path.join(SCRIPT_DIR, "java_utils")

        # paths
        selenium_jar_path = os.path.join(JAVA_UTILS_DIR, "selenium-java-4", "*")  # Path to the Selenium JARs
        chromedriver_path = os.path.join(JAVA_UTILS_DIR, "chromedriver-mac-x64", "chromedriver")  # Path to ChromeDriver

        os.environ["webdriver.chrome.driver"] = chromedriver_path

        sep = ";" if platform.system() == "Windows" else ":"

        classpath = f"{selenium_jar_path}{sep}{tmpdir}"

       # Command to run the Java test automation script
       # Compile the Java file
        compile_command = [
            "javac",
            "-cp", classpath,
            "-d", tmpdir,
            java_file_path
        ]
        compile_process = subprocess.run(compile_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if compile_process.returncode != 0:
            print("Compilation failed:", compile_process.stderr)
            writer({"type": "error", "message": "Compilation failed", "errors": compile_process.stderr})
            writer({"type": "script", "message": state["last_script"]})
            state["messages"].append({"role": "system", "content": f"Script compilation failed: {compile_process.stderr}"})
            state["has_errors"] = True
            state["error_message"] = compile_process.stderr
            return state

        # Run the compiled class
        class_name = os.path.basename(java_file_path).replace(".java", "")
        run_command = [
            "java",
            "-cp", classpath,
            class_name
        ]
        run_process = subprocess.run(run_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if run_process.returncode != 0:
            print("Execution failed:", run_process.stderr)
            writer({"type": "error", "message": "Test execution failed", "errors": run_process.stderr})
            writer({"type": "script", "message": state["last_script"]})
            state["messages"].append({"role": "system", "content": f"Script execution failed: {run_process.stderr}"})
            state["has_errors"] = True
            state["error_message"] = run_process.stderr
        else:
            print("Execution Output:", run_process.stdout)
            writer({"type": "success", "message": "Tests executed successfully"})
            writer({"type": "script", "message": state["last_script"]})
            state["messages"].append({"role": "system", "content": "Script executed successfully"})
            state["has_errors"] = False
    return state

# Function to execute javascript code
def execute_playwright_js_script(state, writer: StreamWriter):
    print("inside execute_playwright_js_script")
    script_content = state["messages"][-1].content
    state["last_script"] = script_content
    language = state.get("language", "javascript")
    print(f"\n=== Generated Script ({language.upper()}) ===")
    print(script_content)
    print("=====================\n")

    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    JS_UTILS_DIR = os.path.join(SCRIPT_DIR, "javascript_utils")

    # Ensure directory exists
    os.makedirs(JS_UTILS_DIR, exist_ok=True)

    if not os.path.exists(os.path.join(JS_UTILS_DIR, "node_modules", "playwright")):
        writer({
            "type": "error",
            "message": "Playwright module not found. Please run `npm install` inside javascript_utils directory."
        })
        state["has_errors"] = True
        return state

    """Execute a JavaScript Playwright test script."""
    # Write the script to a temporary JavaScript file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".spec.js", delete=False, dir=".") as f:
        f.write(script_content)
        temp_path = f.name

    filename = os.path.basename(temp_path)
    new_script_path = os.path.join(JS_UTILS_DIR, filename)
    shutil.move(temp_path, new_script_path)
    
    try:
        writer({"type": "info", "message": "Executing JavaScript test script"})
        print(f"\nRunning Playwright test: npx playwright test {filename}")
        print(f"CWD: {JS_UTILS_DIR}")
        print("=====================\n")
        
        # Run the script using Node.js
        process = subprocess.run(
            ["npx", "playwright", "test", filename],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=JS_UTILS_DIR,
            text=True,
        )
        
        # Check if the process returned an error
        if process.returncode != 0:
            # error_output = process.stderr.strip() or process.stdout.strip()
            error_output = process.stderr if process.stderr else process.stdout
            
            writer({"type": "error", "message": "Test execution failed", "errors": error_output})
            writer({"type": "script", "message": state["last_script"]})
            
            print("\n=== Execution Error ===")
            print(error_output)
            print("=====================\n")
            state["messages"].append(
                {
                    "role": "system",
                    "content": f"Script execution failed with error: {error_output}",
                }
            )
            state["has_errors"] = True
            state["error_message"] = error_output
        else:
            writer({"type": "success", "message": "Tests executed successfully"})
            writer({"type": "script", "message": state["last_script"]})
            print("\n=== Success ===")
            print("Script executed without errors")
            print("=============\n")
            state["messages"].append(
                {"role": "system", "content": "Script executed successfully"}
            )
            state["has_errors"] = False
                
    finally:
        os.unlink(new_script_path)
    return state


# Function defined to handle errors
def handle_errors(state):
    return "retry" if state.get("has_errors", False) else "success"

def limit_error(state):
    # Check if the execution should be stopped
    if state.get("stop_execution", False):
        return "stop"
    
    # Determine which framework to use (Playwright or Selenium)
    framework = state.get("framework")
    language = state.get("language")

    if framework == "selenium":
        return "execute_selenium"
    elif framework == "playwright":
        return "execute_playwright_js" if language == "javascript" else "execute_playwright"
    
def handle_framework(state):
    print("inside handle framework")
    if state["framework"] == "playwright" and state["language"] == "python":
        return "execute_playwright_script"
    elif state["framework"] == "playwright" and state["language"] == "javascript":
        return "execute_playwright_js_script"
    elif state["framework"] == "selenium":
        return "execute_selenium_script"

def retry_with_errors(state, llm,  error_prompt_playwright, error_prompt_selenium, error_prompt_playwright_js, writer: StreamWriter):
    state["retry_count"] = state.get("retry_count", 0) + 1
    max_retries = state["max_retries"]

    writer({"type": "info", "message": f"Refining test script (Attempt {state['retry_count']}/{max_retries})"})
    print("Retry count:", state["retry_count"], "/", max_retries)

    if state["retry_count"] >= max_retries:
        errors = state["messages"][-1].content if state["messages"] else "No script generated."
        writer({
            "type": "error", 
            "message": "Max refinement attempts reached. Please check your test steps and/or the webpage.",
            "details": errors,
            "maxAttempts": True  # Add a flag to identify this specific case
        })

        print("\nMax retries reached. Stopping further refinements.")

        return {
            **state,
            "messages": [{"role": "system", "content": "Test generation failed. Max retries reached."}],
            "stop_execution": True,
            "error_message": "Max retries reached",
        }
    
    else:
        print("\n=== Retrying with error ===")
        print(f"Error message: {state['error_message']}")
        print("========================\n")
        original_script = state.get("last_script", "")

        if state["framework"] == "playwright" and state["language"] == "python":
            print("inside playwright retry")
            prompt = error_prompt_playwright.invoke(
                    {
                        "original_script": original_script,
                        "error_message": state["error_message"],
                        "html_content": state["html_content"],
                        "url": state["url"],
                        "test_steps": state["test_steps"],
                    }
                )

            response = llm.invoke(prompt)
            cleaned_content = clean_script_response(response.content)

            return {
                **state,
                "messages": [{"role": "assistant", "content": cleaned_content}],
                "has_errors": False,
                "error_message": None,
                "max_retries": state["max_retries"],
            }
        elif state["framework"] == "playwright" and state["language"] == "javascript":
            print("inside playwright js retry")
            prompt = error_prompt_playwright_js.invoke(
                    {
                        "original_script": original_script,
                        "error_message": state["error_message"],
                        "html_content": state["html_content"],
                        "url": state["url"],
                        "test_steps": state["test_steps"],
                    }
                )

            response = llm.invoke(prompt)
            cleaned_content = clean_script_response(response.content)

            return {
                **state,
                "messages": [{"role": "assistant", "content": cleaned_content}],
                "has_errors": False,
                "error_message": None,
                "max_retries": state["max_retries"],
            }
        elif state["framework"] == "selenium":
            print("inside selenium retry")
            prompt = error_prompt_selenium.invoke(
                    {
                        "original_script": original_script,
                        "error_message": state["error_message"],
                        "html_content": state["html_content"],
                        "url": state["url"],
                        "test_steps": state["test_steps"],
                    }
                )

            response = llm.invoke(prompt)
            cleaned_content = clean_script_response(response.content)

            return {
                **state,
                "messages": [{"role": "assistant", "content": cleaned_content}],
                "has_errors": False,
                "error_message": None,
                "max_retries": state["max_retries"],
            }

# Function defined to clear the memory after a succesful script execution
def clear_memory(state):
    script_builder.reset()
    
    return {
        **state,
        "messages": [],
        "has_errors": False,
        "error_message": None,
        "execution_time": None,
        "success_rate": None,
        "error_rate": None,
        "retry_count": None,
        "last_script": None,
        "max_retries": None,
        "current_step_index": 0,
        "current_step": None,
        "steps_list": None,
        "completed_steps": [],
        "accumulated_script": None,
        "generated_selectors": {},
        "api_results": {},
        "jira_ticket_id": None,
        "jira_email": None,
        "jira_token": None,
        "jira_domain": None,
    }

# Define custom cache using DiskCache when available
if HAS_CACHE:
    class LLMCache(BaseCache):
        def __init__(self):
            self.cache = DISKCACHE

        def lookup(self, prompt, llm_string):
            return self.cache.get((prompt, llm_string))

        def update(self, prompt, llm_string, return_val):
            self.cache.set((prompt, llm_string), return_val)
