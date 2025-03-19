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

# Define the prompt template
prompt_template = ChatPromptTemplate(
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
error_prompt = ChatPromptTemplate(
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
        "success": "clear", # Route to clear instead of END
    }
)
# Add edges for the necessary transitions
workflow.add_conditional_edges(
    "retry", limit_error, {
        "retry": "execute",  # Continue retrying if needed
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
