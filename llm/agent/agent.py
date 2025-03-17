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
    handle_errors,
    retry_with_errors,
)
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# Load environment variables from .env file
if not load_dotenv():
    raise RuntimeError("Failed to load environment variables from .env file")

# Initialize Azure OpenAI LLM
try:
    llm = AzureChatOpenAI(
        deployment_name=os.getenv("OPENAI_API_DEPLOYMENT"),
        model=os.getenv("OPENAI_API_MODEL"),
        temperature=0.2,
        max_tokens=3000,
    )
except Exception as e:
    raise RuntimeError(f"Failed to initialize Azure OpenAI LLM: {str(e)}")

# Define a new graph
workflow = StateGraph(CustomState)

# Add memory saver instance after the workflow definition
memory_saver = MemorySaver()

# Define the prompt template
prompt_template = ChatPromptTemplate(
    [
        (
            "system",
            """
            You are a test script generator. Generate only a Python Playwright test script for the given HTML content and test steps. Optimize for speed, robustness, and maintainability.
            
            Test Steps:
            {test_steps}
            
            HTML Content:
            {html_content}
            
            URL:
            {url}
            
            Navigation & Waiting:
            - Use `wait_until="domcontentloaded"` for faster page loads unless specific content needs "load".
            - Navigate directly to specific pages when possible (e.g., login page vs homepage→login).
            - Avoid unnecessary waits; use specific element waits with `wait_for(state='visible')`.
            - Avoid "networkidle" waits unless absolutely necessary.
            
            Selector Strategy (prioritized):
            1. Role-based: `get_by_role('button', name='Submit')` 
            2. Text-based: `get_by_text('Log in')`
            3. Test ID: `get_by_test_id('login-button')`
            4. Specific attributes: `locator('[data-cy="submit"]')`
            5. CSS selectors: `locator('.login-form button')`
            6. XPath only when necessary
            
            Performance Optimizations:
            - Use lightweight browser options: `viewport={{'width': 1280, 'height': 720}}`
            - Use keyboard shortcuts when possible (Tab, Enter, Space) instead of clicks
            - Batch assertions to reduce test time
            - Use `expect()` assertions with appropriate matchers for better diagnostics
            
            Reliability Techniques:
            - Add brief retry logic for potentially flaky operations
            - Handle conditional UI elements that may or may not appear
            - Use soft assertions for non-critical checks
            - Filter elements with additional criteria: `.filter(has=page.get_by_text('Submit'))`
            """,
        ),
        MessagesPlaceholder("messages"),
    ]
)


# Define the error prompt template
error_prompt = ChatPromptTemplate(
    [
        (
            "system",
            """
            Fix the following Playwright test script that produced an error. Optimize for speed, reliability, and maintainability.
            
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
            - Generate only the corrected script without explanations.
            - Prioritize **fast and reliable** test execution.
            - Use `wait_until="domcontentloaded"` instead of "load" or "networkidle" when possible.
            - Set `page.set_default_timeout(5000)` at the beginning of tests.
            - Use a module-scoped fixture for browser and context reuse when appropriate.
            - Use `expect()` assertions instead of plain `assert` statements.
            - Use specific selector strategies in this priority order:
            1. Role-based: `get_by_role()`
            2. Text-based: `get_by_text()`
            3. Test ID: `get_by_test_id()`
            4. Stable CSS with `page.locator()`
            5. XPath only when necessary
            
            Error Handling Strategies:
            - For **missing element errors**: Use more reliable selectors or add appropriate wait conditions.
            - For **timeout errors**: Evaluate if the timeout is appropriate or if direct navigation/better selectors can help.
            - For **navigation errors**: Ensure proper waiting for navigations or use direct URLs when possible.
            - For **selector errors**: Provide more specific or resilient selectors.
            - For **assertions errors**: Ensure proper element state before assertion.
            
            Performance Optimizations:
            - Navigate directly to specific pages when possible (e.g., login page vs homepage→login).
            - Use specific element state waits: `wait_for(state='visible')` instead of general page waits.
            - Use lightweight browser options: `viewport={{'width': 1280, 'height': 720}}`.
            - Add retries for potentially flaky operations or network requests.
            """,
        )
    ]
)


# Define nodes
workflow.add_node("home", lambda state, writer: invoke_llm(state, llm, prompt_template, writer))
workflow.add_node("execute", execute_playwright_script)
workflow.add_node("retry", lambda state, writer: retry_with_errors(state, llm, error_prompt, writer))
workflow.add_node("clear", clear_memory)

# Define the flow
workflow.add_edge(START, "home")
workflow.add_edge("home", "execute")

# Add conditional routing based on errors
workflow.add_conditional_edges(
    "execute", handle_errors, {
        "retry": "retry", 
        "success": "clear"  # Route to clear instead of END
    }
)

workflow.add_edge("retry", "execute")
workflow.add_edge("clear", END)

# Compile the workflow
try:
    config = {"memory": memory_saver}
    graph = workflow.compile()
except Exception as e:
    raise RuntimeError(f"Failed to compile workflow: {str(e)}")
