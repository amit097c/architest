import os
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, StateGraph, END
from agent.utils.state import CustomState
from agent.utils.nodes import (
    clear_memory,
    invoke_llm,
    execute_playwright_script,
    execute_selenium_script,
    execute_playwright_js_script,
    handle_errors,
    handle_framework,
    retry_with_errors,
    limit_error,
    initialize_step_execution,
    process_current_step,
    execute_step_script,
    retry_step,
    limit,
    HAS_CACHE
)
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from agent.utils.tools import clean_script_response

# Conditionally import LLMCache if available
if HAS_CACHE:
    from agent.utils.nodes import LLMCache

# Check if running in GitHub Actions
if not os.getenv("GITHUB_ACTIONS"):
    # Load environment variables from .env file (for local testing)
    if not load_dotenv():
        raise RuntimeError("Failed to load environment variables from .env file")
    
# Initialize Azure OpenAI LLM
try:
    # Try to initialize with cache if available
    cache_instance = None
    if HAS_CACHE:
        try:
            cache_instance = LLMCache()
        except Exception as cache_error:
            print(f"Cache initialization failed, continuing without cache: {cache_error}")
    
    llm = AzureChatOpenAI(
        deployment_name=os.getenv("OPENAI_API_DEPLOYMENT"),
        model=os.getenv("OPENAI_API_MODEL"),
        temperature=0.2,
        max_tokens=3000,
        cache=cache_instance,
    )
except Exception as e:
    raise RuntimeError(f"Failed to initialize Azure OpenAI LLM: {str(e)}")

# Define a new graph
workflow = StateGraph(CustomState)

# Add memory saver instance after the workflow definition
memory_saver = MemorySaver()

# Define the prompt template for step-by-step Playwright test generation
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

prompt_template_step = ChatPromptTemplate(
    [
        (
            "system",
            """
            You are an expert QA automation engineer specializing in generating precise and robust **Python Playwright** test steps.

            Your task is to generate a Python function implementing a single test step, adhering strictly to Playwright best practices for element selection.

            ---

            ### 📋 Current Test Step to Implement:
            {current_step}

            ### Previous Context (Actions/State from prior steps, if available):
            {previous_steps_context}

            ### Previously Generated Selectors (for context, if available):
            {selectors_context}

            ### API Results from Previous Steps (if available):
            {api_context}

            ### Script Context So Far (Code generated for previous steps, if available):
            {script_context}

            ### Target URL (Relevant for navigation and context):
            {url}

            ### HTML Content:
            {html_content}

            ---

            ### 🚀 Core Instructions for Generating the Step Function:

            1.  **Function Definition**: Create a function for *this step only*:
                ```python
                def step_X_descriptive_name(page: Page):
                    # Step implementation using Playwright best practices
                    return page # MUST return the page object
                ```
                Replace X with the step number and descriptive_name with a short, meaningful name based on `{current_step}`.

            2.  **DO NOT include imports or test_main function**: Your code will be automatically inserted into a complete test script with proper imports and test_main function.

            3.  **🎯 Element Selection Strategy (CRITICAL - Follow this STRICTLY):**
                * **Goal:** Use selectors that are resilient to code changes and reflect how users interact with the page.
                * **Priority Order (Use the FIRST suitable option):**
                    1.  **`page.get_by_test_id()`**: If `data-testid` (or similar like `data-qa`, `data-cy`) attributes are likely present based on standard practice or visible in the initial HTML, use `page.get_by_test_id("your-test-id")`. **This is highly preferred if available.**
                    2.  **`page.get_by_role()`**: Use ARIA roles (e.g., `button`, `link`, `checkbox`, `heading`) combined with the accessible name (visible text, `aria-label`). Example: `page.get_by_role("button", name="Log In")`. Be precise with the name.
                    3.  **`page.get_by_label()`**: For form elements linked to a visible `<label>`. Example: `page.get_by_label("Username")`.
                    4.  **`page.get_by_text()`**: To find elements by their exact text content. Good for links, buttons, paragraphs. Use `exact=True` for precision where appropriate. Example: `page.get_by_text("Welcome back!", exact=True)`.
                    5.  **`page.get_by_placeholder()`**: For input fields identified by their `placeholder` attribute. Example: `page.get_by_placeholder("Enter your email")`.
                    6.  **`page.get_by_alt_text()`**: For images via their `alt` text.
                    7.  **`page.get_by_title()`**: For elements with a `title` attribute (often tooltips).
                    8.  **CSS / XPath (Last Resort)**: Only use CSS or XPath if *none* of the above user-facing locators are suitable. Prefer simpler, less brittle CSS selectors (e.g., `form#login-form input[name="password"]`) over complex XPath or highly nested selectors.

            4.  **Handling Ambiguity / Multiple Matches**:
                * If a preferred locator (like `get_by_role("button", name="View")`) might match multiple elements, make it unique:
                    * **Filter by Text:** `page.get_by_role("button").filter(has_text="View Details")`
                    * **Filter by Attribute:** `page.get_by_role("link").filter(has_attribute="href", "/products/1")`
                    * **Chain from a Container:** Locate a unique container/parent first, then find the element within it. Example: `container = page.locator("div#user-profile"); edit_button = container.get_by_role("button", name="Edit")`. Use `expect(container).to_be_visible()` before interacting within it.
                    * **Use `.first`, `.last`, or `.nth(index)`:** Only if elements are visually identical and order is stable/intended. Example: `page.get_by_role("button", name="Add to Cart").first`.

            5.  **Actionability Checks**:
                * **ALWAYS** ensure an element is ready before interacting. Use Playwright's `expect` for checks:
                    ```python
                    submit_button = page.get_by_role("button", name="Submit")
                    expect(submit_button).to_be_visible(timeout=10000) # Wait up to 10s
                    expect(submit_button).to_be_enabled()
                    submit_button.click()

                    # For inputs:
                    email_input = page.get_by_label("Email Address")
                    expect(email_input).to_be_visible()
                    expect(email_input).to_be_editable()
                    email_input.fill("[email address removed]")
                    ```

            6.  **API Testing**: If `{current_step}` requires an API call:
                * Use `page.request` context.
                * Print JSON results clearly marked:
                    ```python
                    api_response = page.request.get("/api/users/1")
                    expect(api_response).to_be_ok()
                    response_json = api_response.json()
                    print("\\nAPI_RESULT_START") # Use newline for parser robustness
                    print(json.dumps(response_json, indent=2))
                    print("API_RESULT_END\\n")
                    ```

            7.  **Output Format**: Return ONLY valid Python code for the requested function. No explanations, comments (unless essential for the step implementation), or markdown.
            """
        ),
        MessagesPlaceholder("messages"),
    ]
)

# Revised error prompt template
error_prompt_step = ChatPromptTemplate(
    [
        (
            "system",
            """
            You are an expert QA automation engineer specializing in debugging Python Playwright scripts.

            Your task is to **fix the provided step function** which failed during execution, generating a *more robust* version based on the error and Playwright best practices.

            ---

            ### Failed Script Function:
            ```python
            {original_script}
            ```

            ### ❌ Error Message Encountered:
            ```
            {error_message}
            ```

            ### 📋 Test Step Being Attempted:
            {current_step}

            ### Previous Context (Code generated for steps before the error):
            {script_context}

            ### Previously Generated Selectors (Potentially useful for context):
            {selectors_context}

            ### Target URL:
            {url}

            ### HTML Content:
            {html_content}

            ---

            ### 🛠️ Debugging and Correction Guidelines:

            1.  **Analyze the Error**:
                * **"TimeoutError: waiting for selector..." or "...to be visible/enabled..."**: The locator couldn't find the element OR the element wasn't interactable in time. The selector itself is likely wrong or needs adjustment.
                * **"strict mode violation: selector resolved to N elements..."**: The locator is too general and matched multiple elements. It needs to be made more specific.
                * Other errors: Address based on the specific message (e.g., wrong interaction type).

            2.  **Apply Best Practices for Robust Selectors (Priority Order):**
                * **Re-evaluate the failed selector** in the script above based on these priorities:
                    1.  `get_by_test_id()`: Check if a test ID could be used.
                    2.  `get_by_role()`: Check ARIA role and accessible name. Was the name correct? Is there a better role?
                    3.  `get_by_label()`: Is there a visible label for the form element?
                    4.  `get_by_text()`: Is there unique, stable text content? Try `exact=True`.
                    5.  `get_by_placeholder()`: Is the placeholder unique?
                    6.  `get_by_alt_text()` / `get_by_title()`: For images/tooltips.
                    7.  CSS/XPath: If necessary, simplify or improve the existing CSS/XPath.
                * **Choose the *next best alternative* from the list above** that avoids the issue described in the error message.

            3.  **Fixing "Multiple Elements Found" Errors**:
                * Make the selector more specific using the strategies below:
                    * **Chain from Container**: Identify a unique parent/container (`form`, `div#msodal`, `section[aria-label="User Settings"]`) and locate the element *within* it. `container = page.locator(...); element = container.get_by_role(...)`. Add `expect(container).to_be_visible()`.
                    * **Filter**: Add `.filter(has_text="...")` or `.filter(has=page.locator(...))` to narrow down results.
                    * **Exact Text**: Use `exact=True` with `get_by_text`.
                    * **Positional**: Use `.first`, `.last`, `.nth()` *only* if the ambiguity is due to identical elements where order is meaningful.

            4.  **Fixing "Element Not Found" / Timeout Errors**:
                * **Verify Selector Choice**: Did the original script use the best locator type (e.g., used CSS instead of `get_by_role`)? Switch to a better one from the priority list.
                * **Check for Typos/Case Sensitivity**: Ensure names, text, IDs are exact matches.
                * **Consider Containers/Modals**: Was the element inside a specific section or modal that needs to be located first?
                * **Timing**: Increase timeout for `to_be_visible()` or use `wait_for_load_state()` to ensure page loaded. Use `try/except` with multi-attempt approach for highly dynamic content.

            5.  **Actionability Checks**: Ensure the corrected code still includes `expect(locator).to_be_visible()`, `expect(locator).to_be_enabled()`, etc., *before* interaction methods like `.click()` or `.fill()`.

            6.  **Output**: Return ONLY the corrected Python function for the *failed step*. No explanations, comments (unless essential placeholders), or markdown formatting. Keep the original function signature (`def step_X...`).
            """
        )
    ]
)

# Define the prompt template for Playwright
prompt_template_playwright = ChatPromptTemplate(
    [
        (
            "system",
            """
            You are an expert QA automation engineer.

            Your task is to generate a **Python Playwright test** using the **pytest** framework.
            
            ---
            
            ### Analysis and Test Generation Process:
            1. FIRST: Analyze the provided HTML to identify the most reliable selectors for each element.
            2. SECOND: Determine the most appropriate locator strategy for each element.
            3. THIRD: Generate a test with fallback mechanisms for unreliable elements.

            ---

            ### 📋 Test Details:
            - **Test Steps**:
            {test_steps}

            - **HTML Content**:
            {html_content}

            - **Target URL**:
            {url}

            ---

            ### ⚙️ Guidelines:

            #### ✅ Imports
            Start with:
            ```python
            import pytest
            from playwright.sync_api import Page, expect
            ```

            #### 🧪 Test Function
            ```python
            def test_name(page: Page):
            ```

            #### Locator Strategy Decision Tree:
            - For elements with data-testid: Use `page.get_by_test_id("...")`
            - For interactive elements with accessible roles: Use `page.get_by_role("...", name="...")`
            - For form elements with labels: Use `page.get_by_label("...")`
            - For elements with unique text: Use `page.get_by_text("...", exact=True)`
            - If multiple matching elements exist: Use parent context to narrow selection
            
            #### Resilient Test Pattern:
            - Always include multiple ways to locate critical elements
            - Use wait operations between all interactions
            - Include retry logic for flaky elements
            - Add comments explaining the locator strategy choices
            - Lower the timeouts for faster retries: Use `timeout=10000` for locating elements when necessary
            
            #### 🧼 Output
            Only return valid **Python code** using **pytest** and **Playwright**.  
            **No explanations, markdown, or extra text.**

            ---
            """
        ),
        MessagesPlaceholder("messages"),
    ]
)

# Define the error prompt template for Playwright
error_prompt_playwright = ChatPromptTemplate(
    [
        (
            "system",
            """
            You are an expert QA automation engineer.

            Fix the following **Playwright test script** that produced an error.

            ### 🔧 Problem Context:
            - **Current Script**:
            {original_script}

            - **Error Message**:
            {error_message}

            - **Test Steps**:
            {test_steps}

            - **HTML Content**:
            {html_content}

            - **Target URL**:
            {url}

            ---

            ### ⚙️ Guidelines for Fixing the Script:
            
            #### 🔍 Common causes for Playwright errors:
            - Element not found or hidden
            - Multiple elements matching

            #### 🔍 Locator Improvements
            1. Use the **most specific locators available**, in this order:
                - `page.get_by_test_id("...")` (preferred)
                - `page.get_by_role("...", name="...", exact=True)`
                - `page.get_by_label("...")`
                - `page.get_by_placeholder("...")`
                - `page.get_by_alt_text("...")`
                - `page.get_by_title("...")`
                - `page.get_by_text("...", exact=True)` - **Only use this if no other option uniquely identifies the element.**
            2. Avoid generic locators like `button`, `a`, `div`, or `:root`.
            3. For **hidden elements**, ensure necessary actions (e.g., clicking dropdowns, toggles) are performed first.
            4. If locators match multiple elements, make them more specific using:
                - Parent context (e.g., `section:has(...)`)
                - Attribute filters (e.g., `data-testid`, `data-attribute`)
                - Indexing only as a last resort (e.g., `.nth(0)`).
            5. If `get_by_text("...")` matches multiple elements:
                - Try `get_by_role(..., name=..., exact=True)` instead
                - Use attributes like `data-testid`, `class`, or refine with parent locators
                - Use `.nth(n)` **only if unavoidable**, and **only with a comment** explaining why

            #### ⏳ Handling Timeouts
            - For elements not found, ensure:
                - Lower the default timeout: `page.wait_for_selector("selector", timeout=10000)`
                - Proper waiting: `expect(locator).to_be_visible(timeout=10000)`
                - Element readiness: `locator.scroll_into_view_if_needed()`
                - Consider increasing the timeout in case of complex UI loads, but prioritize shorter timeouts where possible.

            #### 🧪 Output Requirements
            - Return ONLY the corrected Python script using **pytest** and **Playwright**.
            - DO NOT include any explanations, markdown formatting, or additional text.
            - DO NOT include phrases like "Here is the corrected script" or similar.
            - Start directly with the Python code, beginning with imports.
            - Ensure all locators are improved and errors are addressed.
            - Use clean, readable formatting for all Playwright code.

            ---
            """
        )
    ]
)

# Define the prompt template for Selenium
prompt_template_selenium = ChatPromptTemplate(
    [
        (
            "system",
            """
            Generate a Java Selenium test script based on the provided HTML content, URL, and test steps.
            Test Steps:
            {test_steps}

            HTML Content:
            {html_content}

            URL:
            {url}
            
            Constraints:
            - Use Java and import the necessary Selenium, WebDriver, WebDriverWait, and ExpectedConditions classes.    
            - Dont set path of chrome driver, it is already configured.
            - Implement **explicit waits** instead of hardcoded sleep (`Thread.sleep`).  
            - **Analyze the HTML content** to determine the most stable **XPath or CSS Selectors**. 
            - For a successful run, add System.exit(0) right after driver.quit() line to close the browser, and for a failure, add System.exit(1).
            - Ensure proper **exception handling** for timeout, element not found, and stale elements.  
            - Use a try-finally block to ensure the browser is properly closed after execution.
            """,
        ),
        MessagesPlaceholder("messages"),
    ]
)

# Define the error prompt template for Selenium
error_prompt_selenium = ChatPromptTemplate(
    [
        (
            "system",
            """
            You are a Selenium test script debugger. Your task is to fix the following Selenium test script that encountered an error.
            
            Current script:
            {original_script}
            
            Current error:
            {error_message}

            Test Steps:
            {test_steps}
            
            HTML Content:
            {html_content}

            URL:
            {url}
            
            Constraints:
            - **Do NOT explain** the changes, just provide the corrected Java Selenium test script.  
            - **Fix any incorrect XPath or CSS selectors** based on the provided HTML content.  
            - Dont set path of chrome driver, it is already configured.
            - Use **WebDriverWait** instead of `Thread.sleep`.  
            - Implement **proper exception handling** (`try-catch`) to prevent crashes.  
            - Close the WebDriver properly using `try-finally` to avoid resource leaks.  
            - **Avoid solutions that failed in previous attempts.**  

            """,
        )
    ]
)

# Define JavaScript prompt template for Playwright
prompt_template_playwright_js = ChatPromptTemplate(
    [
        (
            "system",
            """
            You are a JavaScript Playwright test script generator. Generate only a JavaScript Playwright test script for the given HTML content and test steps, remember to wait for pages to load.

            Test Steps:
            {test_steps}

            HTML Content:
            {html_content}

            URL:
            {url}
            
            Constraints:
            - Use Playwright's best practices with JavaScript.
            - Analyze the HTML content to identify the necessary selectors.
            - Ensure the script is robust and handles common edge cases.
            - Set appropriate timeouts for actions based on their complexity or 10s as default.
            - Ensure the test cases run in headless mode.
            - Use async/await syntax for better readability and error handling.
            - Export the test function for proper test runner integration.
            """,
        ),
        MessagesPlaceholder("messages"),
    ]
)

# Define JavaScript error prompt template for Playwright
error_prompt_playwright_js = ChatPromptTemplate(
    [
        (
            "system",
            """
            Fix the following JavaScript Playwright test script that produced an error.
            
            Current script:
            {original_script}
            
            Current error:
            {error_message}

            Test Steps:
            {test_steps}
            
            HTML Content:
            {html_content}

            URL:
            {url}
            
            Constraints:
            - Generate only the corrected JavaScript script without any explanations.
            - Avoid solutions that failed in previous attempts.
            - Analyze the HTML content to identify the necessary selectors.
            - Set appropriate timeouts for actions based on their complexity or 10s as default.
            - Ensure the test cases run in headless mode.
            - Use async/await syntax for better readability and error handling.
            - Export the test function for proper test runner integration.
            """,
        )
    ]
)

# Define the step-by-step workflow
step_workflow = StateGraph(CustomState)

# Define nodes for step-by-step workflow
step_workflow.add_node("initialize", lambda state, writer: initialize_step_execution(state, writer))
step_workflow.add_node("process_step", lambda state, writer: process_current_step(state, llm, prompt_template_step, writer))
step_workflow.add_node("execute_step", lambda state, writer: execute_step_script(state, writer))
step_workflow.add_node("retry_step", lambda state, writer: retry_step(state, llm, error_prompt_step, writer))
# step_workflow.add_node("check_stop", lambda state, writer: check_stop(state, writer))
step_workflow.add_node("clear", clear_memory)

# Define the flow for step-by-step workflow
step_workflow.add_edge(START, "initialize")
step_workflow.add_edge("initialize", "process_step")
step_workflow.add_edge("process_step", "execute_step")
step_workflow.add_conditional_edges(
    "retry_step", limit, {
        "stop": "clear",
        "retry": "execute_step",
    }
)
step_workflow.add_edge("clear", END)

# Add conditional edges based on execution results
class StepRouter:
    def __call__(self, state):
        # Check if we need to stop execution
        if state.get("stop_execution", False):
            return "stop"

        # If there are errors, retry
        if state.get("has_errors", False):
            return "retry"
        
        # Check if we've completed all steps
        next_step_index = state["current_step_index"]
        
        # If we're at the last step and it was executed successfully, return "complete"
        if next_step_index >= len(state["steps_list"]) and state["has_errors"] == False:
            return "complete"
            
        # If we have more steps, continue to the next one
        if next_step_index < len(state["steps_list"]):
            state["current_step_index"] = next_step_index
            state["current_step"] = state["steps_list"][next_step_index]
            return "continue"
        
        # Otherwise, stay on the current step (should not happen normally)
        return "continue"

step_workflow.add_conditional_edges(
    "execute_step", 
    StepRouter(),
    {
        "retry": "retry_step",
        "continue": "process_step",
        "complete": "clear",
        "stop": "clear"
    }
)

# Define nodes for legacy workflow (single-step generation)
workflow.add_node("home", lambda state, writer: invoke_llm(state, llm, prompt_template_playwright, prompt_template_selenium, prompt_template_playwright_js, writer))
workflow.add_node("execute_playwright", lambda state, writer: execute_playwright_script(state, writer))
workflow.add_node("execute_selenium", lambda state, writer: execute_selenium_script(state, writer))
workflow.add_node("execute_playwright_js", lambda state, writer: execute_playwright_js_script(state, writer))
workflow.add_node("retry", lambda state, writer: retry_with_errors(state, llm, error_prompt_playwright, error_prompt_selenium, error_prompt_playwright_js, writer))
workflow.add_node("clear", clear_memory)

# Define the flow for legacy workflow
workflow.add_edge(START, "home")
workflow.add_conditional_edges("home", handle_framework, {
    "execute_playwright_script": "execute_playwright",
    "execute_selenium_script": "execute_selenium",
    "execute_playwright_js_script": "execute_playwright_js"
})

workflow.add_conditional_edges(
    "execute_playwright", handle_errors, {
        "retry": "retry", 
        "success": "clear",
    }
)

workflow.add_conditional_edges(
    "execute_selenium", handle_errors, {
        "retry": "retry", 
        "success": "clear",
    }
)

workflow.add_conditional_edges(
    "execute_playwright_js", handle_errors, {
        "retry": "retry", 
        "success": "clear",
    }
)

workflow.add_conditional_edges(
    "retry", limit_error, {
        "execute_selenium": "execute_selenium",
        "execute_playwright": "execute_playwright",
        "execute_playwright_js": "execute_playwright_js",
        "stop": "clear"
    }
)

workflow.add_edge("clear", END)

# Compile the workflows
try:
    config = {"memory": memory_saver}
    graph = workflow.compile()
    step_graph = step_workflow.compile()
except Exception as e:
    raise RuntimeError(f"Failed to compile workflow: {str(e)}")

# Export both graphs
__all__ = ["graph", "step_graph"]
