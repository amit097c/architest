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
            You are a senior QA automation engineer writing **Java (Selenium WebDriver)** test step methods.

            Your task is to generate a **single Java method** implementing the test step described below, following modern Selenium best practices and ensuring maximum robustness.

            ---

            ### 📋 Current Test Step to Implement:
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

            ### 🚀 Critical Implementation Guidelines:

            1. **Function Signature**:
                ```java
                public void stepX_descriptiveName(WebDriver driver) {{
                    // step implementation
                }}
                ```
                - Replace `X` with the step number.
                - Replace `descriptiveName` with a short description based on `{current_step}`.

            2. **Locator Strategy (Priority Order)**:
                - Prefer `By.cssSelector("[data-testid='id']")` for stable attributes.
                - If not available, use `By.linkText("text")` or `By.xpath("//tag[contains(text(),'Text')]")` for visible text.
                - Fallbacks: `By.name`, `By.id`, `By.className`.
                - Never default to XPath unless necessary.

            3. **Explicit Waits**:
                - Always use `WebDriverWait` for visibility and clickability:
                ```java
                WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(15));
                WebElement element = wait.until(ExpectedConditions.visibilityOfElementLocated(By.cssSelector("...")));
                wait.until(ExpectedConditions.elementToBeClickable(element));
                ```

            4. **Scroll Handling**:
                - If the element is not immediately visible:
                ```java
                ((JavascriptExecutor) driver).executeScript("arguments[0].scrollIntoView({{block: 'center'}});", element);
                sleep(500);
                ```

            5. **Handling Ambiguity / Multiple Matches**:
                - If multiple elements match the locator:
                    - **Filter by Text**:
                        ```java
                        List<WebElement> elements = driver.findElements(By.cssSelector("..."));
                        WebElement target = elements.stream()
                            .filter(e -> e.getText().trim().equals("Expected Text"))
                            .findFirst()
                            .orElseThrow(() -> new RuntimeException("Element not found"));
                        ```
                    - **Filter by Attribute**:
                        ```java
                        WebElement target = elements.stream()
                            .filter(e -> "expected-href".equals(e.getAttribute("href")))
                            .findFirst()
                            .orElseThrow(() -> new RuntimeException("Element not found"));
                        ```
                    - **Chain from a Container**:
                        ```java
                        WebElement container = driver.findElement(By.id("container-id"));
                        WebElement target = container.findElement(By.xpath(".//tag[contains(text(),'Text')]"));
                        ```

            6. **Action After Wait**:
                - Click or interact only after visibility and clickability are confirmed.

            7. **Navigation or Page Load Wait**:
                - If the click triggers navigation, wait for the page load:
                ```java
                wait.until(webDriver -> ((JavascriptExecutor) webDriver).executeScript("return document.readyState").equals("complete"));
                ```

            8. **Sleep Usage**:
                - Always use the existing `sleep(long millis)` helper method after scroll and page transitions.

            9. **Output Rules**:
                - Only return the Java method code, no imports, no extra comments unless essential.

            Example method:
            ```java
            public void step1_clickSubmitButton(WebDriver driver) {{
                WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(15));
                JavascriptExecutor jsExecutor = (JavascriptExecutor) driver;

                WebElement submitButton = wait.until(ExpectedConditions.visibilityOfElementLocated(By.id("submit")));
                jsExecutor.executeScript("arguments[0].scrollIntoView({{block: 'center'}});", submitButton);
                sleep(500);

                wait.until(ExpectedConditions.elementToBeClickable(submitButton)).click();
                wait.until(webDriver -> ((JavascriptExecutor) webDriver).executeScript("return document.readyState").equals("complete"));
            }}
            ```
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
            You are a senior QA engineer specializing in debugging and improving **Java Selenium WebDriver** test step methods.

            Your task is to **fix** the provided Java method that failed, using Selenium best practices for robustness, visibility, and dynamic page handling.

            ---

            ### 🧪 Failing Java Method:
            ```java
            {original_script}
            ```

            ### ❌ Error Encountered:
            ```
            {error_message}
            ```

            ### 📋 Test Step:
            {current_step}

            ### Previous Context:
            {script_context}

            ### Known Selectors:
            {selectors_context}

            ### Target URL:
            {url}

            ### HTML Snapshot:
            {html_content}

            ---

            ### 🛠️ Fixing Guidelines:

            1. **Analyze the Error**:
                - Timeout = probably wrong locator or missing wait.
                - Element not interactable = scrolling needed.
                - Page not loaded = missing wait for `document.readyState`.

            2. **Fix Locator Issues**:
                - If locator failed, reselect using:
                    1. `By.cssSelector("[data-testid='id']")`
                    2. `By.linkText("Text")`
                    3. `By.xpath("//tag[contains(text(),'Text')]")`
                    4. `By.name`, `By.id`, `By.className`

            3. **Fix Scroll and Sleep**:
                - Scroll the target element into view and apply:
                ```java
                ((JavascriptExecutor) driver).executeScript("arguments[0].scrollIntoView({{block: 'center'}});", element);
                sleep(500);
                ```

            4. **Fix Multiple Matches**:
                - Use `findElements` and stream filter to disambiguate by text or attribute.

            5. **Fix Waits**:
                - Ensure `visibilityOfElementLocated` and `elementToBeClickable` are used.

            6. **Wait for Page Load** (after navigations):
                - Wait until `document.readyState == 'complete'` after critical actions.

            7. **Final Output**:
                - Only return the corrected Java method code.
                - Keep same function signature (`public void stepX_descriptiveName(WebDriver driver)`).
                - Wrap method body in double curly braces `{{ ... }}`.

            Example fixed method:
            ```java
            public void step2_clickInterviewProcessButton(WebDriver driver) {{
                WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(15));
                JavascriptExecutor jsExecutor = (JavascriptExecutor) driver;

                jsExecutor.executeScript("window.scrollBy(0, 800);");
                sleep(1000);

                WebElement interviewButton = wait.until(ExpectedConditions.visibilityOfElementLocated(By.linkText("interview process")));
                jsExecutor.executeScript("arguments[0].scrollIntoView({{block: 'center'}});", interviewButton);
                sleep(500);

                wait.until(ExpectedConditions.elementToBeClickable(interviewButton)).click();
            }}
            ```
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

__all__ = [
    "prompt_template_step",
    "error_prompt_step",
    "prompt_template_selenium",
    "error_prompt_selenium",
    "prompt_template_playwright_js",
    "error_prompt_playwright_js", 
    "prompt_template_postman",
    "error_prompt_postman"
]