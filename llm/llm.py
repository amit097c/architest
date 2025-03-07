import os
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph, END
from typing import Annotated, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import requests
import tempfile
import subprocess
import asyncio
import re

# Load environment variables from .env file
load_dotenv()


# Update the CustomState class to include has_errors and error_message
class CustomState(TypedDict):
    messages: Annotated[list, add_messages]
    url: str
    test_steps: str
    html_content: Optional[str]
    has_errors: Optional[bool]
    error_message: Optional[str]


# Initialize Azure OpenAI LLM
llm = AzureChatOpenAI(
    deployment_name=os.getenv("OPENAI_API_DEPLOYMENT"),
    model=os.getenv("OPENAI_API_MODEL"),
    temperature=0.8,
    max_tokens=1000,
)

# Define a new graph
workflow = StateGraph(CustomState)

# Add memory saver instance after the workflow definition
memory_saver = MemorySaver()


def clean_script_response(response: str) -> str:
    """Remove Markdown code block syntax from the script response"""
    # Remove ```python at the start and ``` at the end
    cleaned = re.sub(r"^```python\n", "", response)
    cleaned = re.sub(r"\n```$", "", cleaned)
    # Also handle case where it's just ``` without python
    cleaned = re.sub(r"^```\n", "", cleaned)
    return cleaned.strip()


def retrieve_examples(query: str, examples_dir: str = "examples") -> list:
    examples = []
    for filename in os.listdir(examples_dir):
        if filename.endswith(".py"):
            with open(os.path.join(examples_dir, filename), "r") as file:
                content = file.read()
                if query.lower() in content.lower():
                    examples.append(content)
    return examples


def invoke_llm(state: CustomState):
    query = f"Generate Playwright test for {state['test_steps']}"
    examples = retrieve_examples(query)

    prompt_template = ChatPromptTemplate(
        [
            (
                "system",
                """
         You are a test script generator. Generate only headless Python Playwright test script for the given HTML content and test steps, remember to wait for pages to load. 
         Do not include any explanations, comments, or additional text.

        Test Steps:
        {test_steps}

        HTML Content:
        {html_content}

        Here are some examples of good Python Playwright test scripts:
        {examples}
        
        Constraints:
        - Use Playwright's best practices.
        - Ensure the script is robust and handles common edge cases.
        - Optimize for performance and readability.
        """,
            ),
            MessagesPlaceholder("messages"),
        ]
    )
    prompt = prompt_template.invoke(
        {
            "test_steps": state["test_steps"],
            "html_content": state["html_content"],
            "examples": "\n\n".join(examples),
            "messages": state["messages"],
        }
    )
    response = llm.invoke(prompt)
    cleaned_content = clean_script_response(response.content)
    return {"messages": [{"role": "assistant", "content": cleaned_content}]}


def extract_html(state: CustomState) -> CustomState:
    """Extract HTML from the provided URL"""
    url = state["url"]
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        html_content = response.text
        state["html_content"] = html_content
        state["messages"].append(
            {"role": "system", "content": f"Successfully extracted HTML from {url}."}
        )
    except Exception as e:
        state["messages"].append(
            {"role": "system", "content": f"Failed to extract HTML: {str(e)}"}
        )
    return state


def is_async_script(script_content: str) -> bool:
    """Check if the script contains async/await keywords"""
    return bool(re.search(r"\basync\s+def\b", script_content))


def execute_playwright_script(state: CustomState) -> CustomState:
    """Execute the generated Playwright script and capture any errors"""
    script_content = state["messages"][-1].content
    print("\n=== Generated Script ===")
    print(script_content)
    print("=====================\n")

    # Create temporary file for the script
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        if is_async_script(script_content):
            # Wrap async script in asyncio run
            wrapper_script = f"""
            import asyncio
            {script_content}

            test_func = [f for f in locals().values() if callable(f) and f.__name__.startswith('test_')][0]
            asyncio.run(test_func())
            """
            f.write(wrapper_script)
        else:
            f.write(script_content)
        temp_path = f.name

    try:
        process = subprocess.run(["python", temp_path], capture_output=True, text=True)
        if process.returncode != 0:
            print("\n=== Execution Error ===")
            print(process.stderr)
            print("=====================\n")
            state["messages"].append(
                {
                    "role": "system",
                    "content": f"Script execution failed with error: {process.stderr}",
                }
            )
            state["has_errors"] = True
            state["error_message"] = process.stderr
        else:
            print("\n=== Success ===")
            print("Script executed without errors")
            print("=============\n")
            state["messages"].append(
                {"role": "system", "content": "Script executed successfully"}
            )
            state["has_errors"] = False
    finally:
        os.unlink(temp_path)
    return state


def handle_errors(state: CustomState) -> str:
    """Route to either success or retry based on errors"""
    return "retry" if state.get("has_errors", False) else "success"


def retry_with_errors(state: CustomState) -> CustomState:
    """Send the script and error back to LLM for correction"""
    print("\n=== Retrying with error ===")
    print(f"Error message: {state['error_message']}")
    print("========================\n")

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
         
         Generate only the corrected script without any explanations.
         Avoid solutions that failed in previous attempts.
         """,
            )
        ]
    )

    prompt = error_prompt.invoke(
        {
            "original_script": state["messages"][-2].content,
            "error_message": state["error_message"],
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
    }


# Update the workflow graph structure at the bottom of the file
workflow = StateGraph(CustomState)

# Define nodes
workflow.add_node("extract_html", extract_html)
workflow.add_node("home", invoke_llm)
workflow.add_node("execute", execute_playwright_script)
workflow.add_node("retry", retry_with_errors)

# Define the flow
workflow.add_edge(START, "extract_html")
workflow.add_edge("extract_html", "home")
workflow.add_edge("home", "execute")

# Add conditional routing based on errors
workflow.add_conditional_edges(
    "execute", handle_errors, {"retry": "retry", "success": END}
)

workflow.add_edge("retry", "execute")

# Compile the workflow
config = {"memory": memory_saver}
graph = workflow.compile()
