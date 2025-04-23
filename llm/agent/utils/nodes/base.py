from langgraph.types import StreamWriter
from langgraph.graph import END
from .builders import PlaywrightTestStep, JavaScriptTestStep, JavaTestStep, ScriptBuilder, ScriptBuilderJS, ScriptBuilderJava, get_script_builder, set_script_builder
from agent.utils.tools import clean_script_response
from typing import List, Dict, Any
from playwright.async_api import async_playwright
import json
import asyncio
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

# Function to initialize the step-by-step test execution
def initialize_step_execution(state, writer: StreamWriter):
    """Initialize test execution and set up appropriate script builder."""
    writer({"type": "info", "message": "Initializing step-by-step test execution"})
    
    steps_list = [step.strip() for step in state["test_steps"].strip().split('\n') if step.strip()]
    framework = state.get("framework", "playwright")
    language = state.get("language", "python")
    
    if framework == "postman":
        updated_state = {
            "current_step_index": 0,
            "steps_list": steps_list,
            "current_step": steps_list[0] if steps_list else None,
            "completed_steps": [],
            "accumulated_script": "",
        }
        return {**state, **updated_state}

    # Initialize appropriate builder
    if framework == "playwright" and language == "python":
        builder = ScriptBuilder()
    elif framework == "playwright" and language == "javascript":
        builder = ScriptBuilderJS()
    elif framework == "selenium":
        builder = ScriptBuilderJava()
    else:
        raise ValueError(f"Unsupported combination: {framework} + {language}")

    # Set URL and store builder
    if builder:
        builder.set_url(state["url"])
        set_script_builder(builder)  # Set global builder instance

    # Return updated state
    return {**state, **{
        "current_step_index": 0,
        "steps_list": steps_list,
        "current_step": steps_list[0] if steps_list else None,
        "completed_steps": [],
        "accumulated_script": "",
        "generated_selectors": {},
        "api_results": {},
    }}

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



# Function to process the current test step
def process_current_step(state, llm, prompt_template_step, prompt_template_selenium, prompt_template_playwright_js, prompt_template_postman, writer: StreamWriter):
    writer({"type": "info", "message": f"Processing step {state['current_step_index'] + 1}/{len(state['steps_list'])}: {state['current_step']}"})
    
    is_first_step = state["current_step_index"] == 0

    previous_steps_context = ""
    if state.get("completed_steps"):
        previous_steps_context = "Previous completed steps:\n"
        for i, step in enumerate(state["completed_steps"]):
            previous_steps_context += f"{i+1}. {step}\n"

    selectors_context = ""
    if state.get("generated_selectors"):
        selectors_context = "Previously generated selectors:\n"
        for element, selector in state["generated_selectors"].items():
            selectors_context += f"- {element}: {selector}\n"

    api_context = ""
    if state.get("api_results"):
        api_context = "API results from previous steps:\n"
        api_context += json.dumps(state["api_results"], indent=2)

    script_context = state.get("accumulated_script", "")

    html_content = state.get("html_content")
    selector_data = []

    if is_first_step and html_content:
        try:
            selector_data = asyncio.run(preprocess_html_for_selectors(html_content, state["url"]))
            if selector_data:
                for item in selector_data:
                    text = item["text"]
                    best_selector = item["selectors"][0]["selector"] if item["selectors"] else None
                    if best_selector:
                        state.setdefault("generated_selectors", {})[text] = best_selector
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

    framework = state.get("framework", "playwright")
    language = state.get("language", "python")
    
    if framework == "postman":
        prompt_vars = {
            "api_endpoint": state.get("api_endpoint", ""),
            "api_method": state.get("api_method", "GET"),
            "api_payload": state.get("api_payload", "{}"),
            "test_steps": state["current_step"]
        }
    else:
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

    prompt_templates = {
    ("playwright", "python"): prompt_template_step,
    ("playwright", "javascript"): prompt_template_playwright_js,
    ("selenium", "java"): prompt_template_selenium,
    ("postman",): prompt_template_postman,
    }

    template_key = (framework, language) if framework != "postman" else ("postman",)
    template = prompt_templates.get(template_key)
    
    base_prompt = template.invoke(prompt_vars)
    
    # enhanced_prompt = rag_manager.enhance_prompt(
    #     framework=state["framework"],
    #     test_steps=state["current_step"],
    #     html_content=state["html_content"],
    #     base_prompt=base_prompt
    # )
    
    response = llm.invoke(base_prompt)
    cleaned_content = clean_script_response(response.content)

    if framework == "postman":
        return {
            "messages": [{"role": "assistant", "content": cleaned_content}],
            "max_retries": state["max_retries"],
            "last_script": cleaned_content,
        }
    if framework == "playwright" and language == "python":
        test_step = PlaywrightTestStep(cleaned_content, state["current_step"])
    elif framework == "playwright" and language == "javascript":
        test_step = JavaScriptTestStep(cleaned_content, state["current_step"])
    elif framework == "selenium":
        test_step = JavaTestStep(cleaned_content, state["current_step"])
    else:
        raise ValueError("Unsupported framework/language")
    
    # Replace direct script_builder reference with getter
    script_builder = get_script_builder()
    if not script_builder:
        raise RuntimeError("Script builder not initialized")
    
    script_builder.add_step(test_step)
    
    return {
        "messages": [{"role": "assistant", "content": cleaned_content}],
        "max_retries": state["max_retries"],
        "last_script": cleaned_content,
    }

def retry_step(state, llm, error_prompt_step, error_prompt_playwright_js, error_prompt_selenium, error_prompt_postman, writer: StreamWriter):
    """Retry the current failed step with error information."""

    state["retry_count"] = state.get("retry_count", 0) + 1
    max_retries = state["max_retries"]
    current_step_index = state["current_step_index"]

    writer({"type": "info", "message": f"Refining test script {current_step_index + 1} (Attempt {state['retry_count']}/{max_retries})"})
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

        framework = state.get("framework", "playwright")
        language = state.get("language", "python")

        prompt_templates = {
        ("playwright", "python"): error_prompt_step,
        ("playwright", "javascript"): error_prompt_playwright_js,
        ("selenium", "java"): error_prompt_selenium,
        ("postman",): error_prompt_postman,
        }

        template_key = (framework, language) if framework != "postman" else ("postman",)
        template = prompt_templates.get(template_key)

        if framework == "postman":
            retry_prompt = template.invoke({
                "api_endpoint": state.get("api_endpoint", ""),
                "api_method": state.get("api_method", "GET"),
                "api_payload": state.get("api_payload", "{}"),
                "test_steps": state["current_step"],
                "error_message": error_message,
                "original_script": current_step_function,
            })
        else:
            retry_prompt = template.invoke({
                "original_script": current_step_function,
                "error_message": error_message,
                "current_step": state["current_step"],
                "script_context": accumulated_script,
                "selectors_context": json.dumps(state["generated_selectors"], indent=2),
                "url": state["url"],
                "html_content": state["html_content"],
                "messages": state["messages"],
            })
        
        # Invoke LLM for correction
        response = llm.invoke(retry_prompt)
        cleaned_content = clean_script_response(response.content)
        print(f"cleaned_content: {cleaned_content}")

        if framework == "playwright" and language == "python":
            test_step = PlaywrightTestStep(cleaned_content, state["current_step"])
        elif framework == "playwright" and language == "javascript":
            test_step = JavaScriptTestStep(cleaned_content, state["current_step"])
        elif framework == "selenium":
            test_step = JavaTestStep(cleaned_content, state["current_step"])
        else:
            test_step = None  # postman doesn't use test_step class

        if test_step:
            # Replace direct script_builder reference with getter
            script_builder = get_script_builder()
            if not script_builder:
                raise RuntimeError("Script builder not initialized")
        
            script_builder.replace_last_step(test_step)

        # test_step = PlaywrightTestStep(cleaned_content, state["current_step"])
        # script_builder.replace_last_step(test_step)
        
        # Update state
        return {
            "messages": [{"role": "assistant", "content": cleaned_content}],
            "retry_count": state["retry_count"],
            "last_script": cleaned_content,
        }

def limit(state):
    return "stop" if state.get("stop_execution", False) else "retry"

def limit_error(state):
    # Check if the execution should be stopped
    if state.get("stop_execution", False):
        return "stop"
    
    # Determine which framework to use (Playwright or Selenium)
    framework = state.get("framework")
    language = state.get("language")

    if framework == "selenium":
        return "execute_selenium"
    elif framework == "postman":
        return "execute_postman"
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
    elif state["framework"] == "postman":
        return "execute_postman_collection"

# Function defined to clear the memory after a succesful script execution
def clear_memory(state):
    try:
        # Replace direct script_builder reference with getter
        script_builder = get_script_builder()
        if script_builder:
            script_builder.reset()
    except (NameError, RuntimeError):
        pass
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

__all__ = [
    'initialize_step_execution',
    'process_current_step',
    'retry_step',
    'limit',
    'limit_error',
    'handle_framework',
    'clear_memory',
    'HAS_CACHE',
]
