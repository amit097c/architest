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

prompt_template_playwright = ChatPromptTemplate(
    [
        (
            "system",
            """
            You are a test script generator. Generate only a Python Playwright test script for the given HTML content and test steps, remember to wait for pages to load.

            Test Steps:
            {test_steps}

            HTML Content:
            {html_content}

            URL:
            {url}
            
            Constraints:
            - Use Playwright's best practices.
            - Analyze the HTML content to identify the necessary selectors.
            - Ensure the script is robust and handles common edge cases.
            - Set appropriate timeouts for actions based on their complexity or 10s as default.
            - Ensure the test cases run in headless mode.
            """,
        ),
        MessagesPlaceholder("messages"),
    ]
)


# Define the error prompt template
error_prompt_playwright = ChatPromptTemplate(
    [
        (
            "system",
            """
            Fix the following Playwright test script that produced an error.
            
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
            - Generate only the corrected script without any explanations.
            - Avoid solutions that failed in previous attempts.
            - Analyze the HTML content to identify the necessary selectors.
            - Set appropriate timeouts for actions based on their complexity or 10s as default.
            - Ensure the test cases run in headless mode.
            """,
        )
    ]
)

# Define the prompt template
prompt_template_selenium = ChatPromptTemplate(
    [
        (
            "system",
            """
             You are a Selenium test script generator that produces only Java-based test scripts using best practices.

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


# Define the error prompt template
error_prompt_selenium = ChatPromptTemplate(
    [
        (
            "system",
            """
             You are a Selenium test script debugger. Your task is to fix the following Selenium test script that encountered an error. Fix the following Selenium test script that produced an error.
            
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



# Define nodes
workflow.add_node("home", lambda state, writer: invoke_llm(state, llm, prompt_template_playwright,prompt_template_selenium, prompt_template_playwright_js, writer))
#workflow.add_node("execute_playwright", execute_playwright_script())
workflow.add_node("execute_playwright", lambda state, writer: execute_playwright_script(state, writer))
workflow.add_node("execute_selenium", lambda state, writer: execute_selenium_script(state, writer))
workflow.add_node("execute_playwright_js", lambda state, writer: execute_playwright_js_script(state, writer))

#workflow.add_node("execute_selenium", execute_selenium_script)
workflow.add_node("retry", lambda state, writer: retry_with_errors(state, llm, error_prompt_playwright,error_prompt_selenium, error_prompt_playwright_js, writer))
workflow.add_node("clear", clear_memory)

# Define the flow
workflow.add_edge(START, "home")
#workflow.add_edge("home", "execute")
workflow.add_conditional_edges("home",handle_framework, {
    "execute_playwright_script": "execute_playwright",
    "execute_selenium_script": "execute_selenium",
    "execute_playwright_js_script": "execute_playwright_js"
})

# Add conditional routing based on errors
workflow.add_conditional_edges(
    "execute_playwright", handle_errors, {
        "retry": "retry", 
        "success": "clear", # Route to clear instead of END
    }
)

workflow.add_conditional_edges(
    "execute_selenium", handle_errors, {
        "retry": "retry", 
        "success": "clear", # Route to clear instead of END
    }
)

workflow.add_conditional_edges(
    "execute_playwright_js", handle_errors, {
        "retry": "retry", 
        "success": "clear", # Route to clear instead of END
    }
)

# Add edges for the necessary transitions
workflow.add_conditional_edges(
    "retry", limit_error, {
        "execute_selenium": "execute_selenium",  # Continue retrying if needed
        "execute_playwright": "execute_playwright",  # Continue retrying if needed
        "execute_playwright_js": "execute_playwright_js",  # Continue retrying if needed
        "stop": "clear"  # Stop execution when limit is reached
    }
)

workflow.add_edge("clear", END)

# Compile the workflow
try:
    config = {"memory": memory_saver}
    graph = workflow.compile()
except Exception as e:
    raise RuntimeError(f"Failed to compile workflow: {str(e)}")
