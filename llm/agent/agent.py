import os
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, StateGraph, END
from agent.utils.state import CustomState
from agent.utils.nodes import (
    clear_memory,
    execute_selenium_script,
    execute_playwright_js_script,
    execute_postman_collection,
    handle_framework,
    limit_error,
    initialize_step_execution,
    process_current_step,
    execute_step_script,
    retry_step,
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

# Define the prompt template for Selenium
prompt_template_selenium = ChatPromptTemplate(
    [
        (
            "system",
            """
            You are a senior QA engineer writing **Java (Selenium WebDriver)** test step methods.

            Your task is to write a **single Java method** implementing the test step described below. Follow Selenium best practices and ensure your code is robust and reliable.

            ---

            ### 🚀 Test Step:
            {current_step}

            ### Previous Steps (Context):
            {previous_steps_context}

            ### Known Selectors:
            {selectors_context}

            ### API Context:
            {api_context}

            ### Script So Far:
            {script_context}

            ### Target URL:
            {url}

            ### HTML Snapshot:
            {html_content}

            ---

            ### ✅ Guidelines:

            1. **Method Signature**:
            ```java
            public void stepX_descriptiveName(WebDriver driver) {{
                // step implementation
            }}
            ```

            2. **Element Locators** (in this order):
                - `By.cssSelector("[data-testid='id']")` for stable attributes
                - `By.xpath(...)` or `By.linkText(...)` for unique text
                - `By.name`, `By.id`, or `By.className` as fallback

            3. **Always use explicit waits**:
            ```java
            WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(10));
            WebElement button = wait.until(ExpectedConditions.elementToBeClickable(By.id("submit")));
            button.click();
            ```

            4. **API Interactions (if any)**: Simulate HTTP requests using libraries like OkHttp or RestAssured, but skip actual implementation unless required.

            5. **Return Type**: `void`

            6. Output only valid Java code — no test classes, no `main()` or boilerplate.

            Example return:
            ```java
            public void step1_clickSubmit(WebDriver driver) {{
                WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(10));
                WebElement button = wait.until(ExpectedConditions.elementToBeClickable(By.id("submit")));
                button.click();
            }}
            ```

            Only return the function. No wrapper code or comments unless essential.
            """
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
            You are a professional QA engineer experienced in debugging **Selenium WebDriver tests written in Java**.

            Your task is to FIX the following Java function that failed execution, using Selenium best practices.

            ---

            ### 🧪 Failing Java Method:
            ```java
            {original_script}
            ```

            ### ❌ Error Message:
            ```
            {error_message}
            ```

            ### 📋 Test Step:
            {current_step}

            ### Other Steps Previously Generated:
            {script_context}

            ### Element Selectors Already Used:
            {selectors_context}

            ### Target Page URL:
            {url}

            ### HTML Snapshot:
            {html_content}

            ---

            ### 🔧 Fixing Instructions:

            1. **Selector Problems**:
                - If locator failed, try more stable options:
                    - Prefer `By.id`, `By.name`, or `By.cssSelector` with unique attributes like `data-*`.
                    - Use `By.xpath` only if CSS is insufficient.
                    - Add wait conditions using `WebDriverWait` and `ExpectedConditions`.

            2. **Common Fixes**:
                - Ensure element is visible: 
                    ```java
                    WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(10));
                    WebElement btn = wait.until(ExpectedConditions.visibilityOfElementLocated(By.id("submit")));
                    ```
                - Avoid `Thread.sleep()`. Use `WebDriverWait` instead.
                - Handle overlays, dynamic loading using proper wait conditions.

            3. **Function Format**:
                - Keep the same method signature: `public void step_X_name(WebDriver driver)`
                - Wrap your implementation in double curly braces like:
                    ```java
                    public void step1_clickButton(WebDriver driver) {{
                        // fixed implementation
                    }}
                    ```
                - Do not include imports or class declaration.
                - Return **only the corrected method code** — no markdown, no commentary.
            """
        )
    ]
)


prompt_template_playwright_js = ChatPromptTemplate(
    [
        (
            "system",
            """
            You are an expert QA automation engineer specializing in **JavaScript-based Playwright** tests.

            Your task is to generate an **async JavaScript function** that implements a single test step. Follow best practices for element selection, test structure, and reusability.

            ---

            ### 🧪 Current Test Step to Implement:
            {current_step}

            ### Previous Context (Optional):
            {previous_steps_context}

            ### Selectors So Far:
            {selectors_context}

            ### API Results (if any):
            {api_context}

            ### Script Context So Far:
            {script_context}

            ### Target URL:
            {url}

            ### HTML Snapshot:
            {html_content}

            ---

            ### 🛠️ Instructions for Code Generation:

            1. **Function Signature**:
            ```javascript
            async function step_X_descriptiveName(page) {{
                // implementation
            }}
            ```
            Replace `X` with step number and use a clear `descriptiveName`.

            2. **Don’t include the full test wrapper or imports.** Only the async function.

            3. **Selectors (in order of priority):**
                - `getByTestId()` if test IDs are available.
                - `getByRole()` with `name` for ARIA elements.
                - `getByText()`, `getByLabel()` etc. from Playwright’s testing library.
                - Use `page.locator(...)` with precise CSS if nothing else fits.

            4. **Check visibility/actionability:**
            ```javascript
            const button = page.getByRole('button', {{ name: 'Submit' }});
            await expect(button).toBeVisible();
            await expect(button).toBeEnabled();
            await button.click();
            ```

            5. **Return nothing** — just the function.

            6. **For API assertions**, use:
            ```javascript
            const res = await page.request.get('/api/user');
            expect(res.ok()).toBeTruthy();
            const json = await res.json();
            console.log("\\nAPI_RESULT_START");
            console.log(JSON.stringify(json, null, 2));
            console.log("API_RESULT_END\\n");
            ```

            Output only the function, no extra explanation or test wrapper.
            """
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
            You are a senior QA automation engineer with deep expertise in debugging **Playwright tests written in JavaScript**.

            Your task is to FIX the failing step function provided below using **Playwright best practices** for selectors and timing.

            ---

            ### 🔧 Failed Function (JavaScript):
            ```javascript
            {original_script}
            ```

            ### ❌ Error Encountered:
            ```
            {error_message}
            ```

            ### 📋 Test Step:
            {current_step}

            ### Previously Generated Code (For Context):
            {script_context}

            ### Selectors Previously Used:
            {selectors_context}

            ### Target Page URL:
            {url}

            ### HTML Snapshot (May Help Debug UI Structure):
            {html_content}

            ---

            ### 🛠️ Guidelines for Fixing the Function:

            1. **Locator Improvements**:
                - If the selector failed or matched multiple elements:
                    - Switch to `getByTestId`, `getByRole`, or better alternative.
                    - Use `locator().filter()` or `.nth()` to disambiguate.
                    - Add `await expect(locator).toBeVisible()` or `toBeEnabled()` as necessary.

            2. **Common Fix Patterns**:
                - Use `await expect(...).toBeVisible({{ timeout: 10000 }})` to ensure timing.
                - If interacting with modals/overlays, make sure they’re visible first.
                - Wrap fragile selectors with `try {{ ... }} catch (e) {{}}` if needed.

            3. **Maintain Format**:
                - Keep the same function signature: `async function step_X_name(page)`
                - Return the `page` object at the end.
                - Do not include main test() function or imports.
                - Return **only the corrected function** (no markdown or extra commentary).
            """
        )
    ]
)

# Add API test prompt templates
prompt_template_postman = ChatPromptTemplate([
    ("system", """
    You are a Postman collection JSON generator, generate only a Postman collection JSON for API testing.
    
    API Details:
    Endpoint: {api_endpoint}
    Method: {api_method}
    Payload: {api_payload}
    
    Test Steps:
    {test_steps}
    
    Constraints:
    - Generate valid Postman collection format v2.1
    - Include environment variables where appropriate
    - Add test scripts to validate response status, body, and headers
    - Include error handling and assertions
    """)
])

error_prompt_postman = ChatPromptTemplate([
    ("system", """
    Fix the following Postman collection JSON that produced an error.
    
    Current collection:
    {original_script}
    
    Current error:
    {error_message}

    API Details:
    Endpoint: {api_endpoint}
    Method: {api_method}
    Payload: {api_payload}
    
    Test Steps:
    {test_steps}
    
    Constraints:
    - Return only the generated script without any explanations.
    - Generate valid Postman collection format v2.1
    - Include environment variables where appropriate
    - Add test scripts to validate response status, body, and headers
    - Include error handling and assertions
    """)
])


# Define the step-by-step workflow
step_workflow = StateGraph(CustomState)

# Define nodes for step-by-step workflow
step_workflow.add_node("initialize", lambda state, writer: initialize_step_execution(state, writer))
step_workflow.add_node("process_step", lambda state, writer: process_current_step(state, llm, prompt_template_step, prompt_template_selenium, prompt_template_playwright_js, prompt_template_postman, writer))
step_workflow.add_node("execute_step", lambda state, writer: execute_step_script(state, writer))
step_workflow.add_node("execute_playwright_js", lambda state, writer: execute_playwright_js_script(state, writer))
step_workflow.add_node("execute_selenium", lambda state, writer: execute_selenium_script(state, writer))
step_workflow.add_node("execute_postman", lambda state, writer: execute_postman_collection(state, writer))
step_workflow.add_node("retry_step", lambda state, writer: retry_step(state, llm, error_prompt_step, error_prompt_playwright_js, error_prompt_selenium, error_prompt_postman, writer))
# step_workflow.add_node("check_stop", lambda state, writer: check_stop(state, writer))
step_workflow.add_node("clear", clear_memory)

# Define the flow for step-by-step workflow
step_workflow.add_edge(START, "initialize")
step_workflow.add_edge("initialize", "process_step")
# step_workflow.add_edge("process_step", "execute_step")
step_workflow.add_conditional_edges("process_step", handle_framework, {
    "execute_playwright_script": "execute_step",
    "execute_selenium_script": "execute_selenium",
    "execute_playwright_js_script": "execute_playwright_js",
    "execute_postman_collection": "execute_postman"
})

step_workflow.add_conditional_edges(
    "retry_step", limit_error, {
        "execute_selenium": "execute_selenium",
        "execute_playwright": "execute_step",
        "execute_playwright_js": "execute_playwright_js",
        "execute_postman": "execute_postman",
        "stop": "clear"
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

step_workflow.add_conditional_edges(
    "execute_selenium", 
    StepRouter(),
    {
        "retry": "retry_step",
        "continue": "process_step",
        "complete": "clear",
        "stop": "clear"
    }
)
step_workflow.add_conditional_edges(
    "execute_playwright_js", 
    StepRouter(),
    {
        "retry": "retry_step",
        "continue": "process_step",
        "complete": "clear",
        "stop": "clear"
    }
)
step_workflow.add_conditional_edges(
    "execute_postman", 
    StepRouter(),
    {
        "retry": "retry_step",
        "continue": "process_step",
        "complete": "clear",
        "stop": "clear"
    }
)

# Compile the workflows
try:
    config = {"memory": memory_saver}
    step_graph = step_workflow.compile()
except Exception as e:
    raise RuntimeError(f"Failed to compile workflow: {str(e)}")

# Export both graphs
__all__ = ["step_graph"]
