import os
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, StateGraph, END
from agent.utils.state import CustomState
from agent.utils.nodes import (
    invoke_llm,
    execute_playwright_script,
    handle_errors,
    retry_with_errors,
)
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# Load environment variables from .env file
load_dotenv()

# Initialize Azure OpenAI LLM
llm = AzureChatOpenAI(
    deployment_name=os.getenv("OPENAI_API_DEPLOYMENT"),
    model=os.getenv("OPENAI_API_MODEL"),
    temperature=0.2,
    max_tokens=1000,
)

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
            Do not include any explanations, comments, or additional text.

            Test Steps:
            {test_steps}

            HTML Content:
            {html_content}

            Retrieved Examples:
            {examples}
            
            Constraints:
            - Use Playwright's best practices.
            - Ensure the script is robust and handles common edge cases.
            - Optimize for performance and readability.
            - Set appropriate timeouts for actions based on their complexity.
            - Use a default timeout of 10 seconds for all actions unless specified otherwise.
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
            
            URL to test:
            {url}
            
            Test Steps:
            {test_steps}
            
            Constraints:
            - Generate only the corrected script without any explanations.
            - Avoid solutions that failed in previous attempts.
            - Set appropriate timeouts for actions based on their complexity.
            - Use a default timeout of 10 seconds for all actions unless specified otherwise.
            - Ensure the test cases run in headless mode.
            """,
        )
    ]
)

# Define nodes
# workflow.add_node("extract_html", extract_html)
workflow.add_node("home", lambda state: invoke_llm(state, llm, prompt_template))
workflow.add_node("execute", execute_playwright_script)
workflow.add_node("retry", lambda state: retry_with_errors(state, llm, error_prompt))

# Define the flow
workflow.add_edge(START, "home")
workflow.add_edge("home", "execute")

# Add conditional routing based on errors
workflow.add_conditional_edges(
    "execute", handle_errors, {"retry": "retry", "success": END}
)

workflow.add_edge("retry", "execute")

# Compile the workflow
config = {"memory": memory_saver}
graph = workflow.compile()
