import requests
import tempfile
import subprocess
import os
from agent.utils.tools import clean_script_response, retrieve_examples


def invoke_llm(state, llm, prompt_template):
    # query = f"Generate Playwright test for {state['test_steps']}"
    # examples = retrieve_examples(query)

    prompt = prompt_template.invoke(
        {
            "test_steps": state["test_steps"],
            "html_content": state["html_content"],
            "url": state["url"],
            # "examples": "\n\n".join(examples),
            "messages": state["messages"],
        }
    )
    response = llm.invoke(prompt)
    cleaned_content = clean_script_response(response.content)
    return {"messages": [{"role": "assistant", "content": cleaned_content}]}


def execute_playwright_script(state):
    script_content = state["messages"][-1].content
    print("\n=== Generated Script ===")
    print(script_content)
    print("=====================\n")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        if "async def" in script_content:
            wrapper_script = f"""
import asyncio
from playwright.async_api import async_playwright
{script_content}

test_func = [f for f in locals().values() if callable(f) and f.__name__.startswith('test_')][0]
asyncio.run(test_func())
"""
        else:
            wrapper_script = f"""
from playwright.sync_api import sync_playwright
{script_content}
"""
        f.write(wrapper_script)
        temp_path = f.name

    try:
        # Install dependencies in the current Python environment
        subprocess.run(["pip", "install", "playwright"], check=True, capture_output=True)
        subprocess.run(["playwright", "install", "chromium"], check=True, capture_output=True)
        
        # Run the script with shell=True to ensure proper execution
        process = subprocess.run(
            f"pytest {temp_path}", 
            shell=True,
            capture_output=True,
            text=True,
            env=os.environ.copy()  # Pass current environment
        )

        print("Process", process)
        print("Return code:", process.returncode)
        print("Output:", process.stdout)
        print("Errors:", process.stderr)
        
        # Check for common Playwright error patterns in both stdout and stderr
        # error_patterns = [
        #     "Error:", 
        #     "TimeoutError", 
        #     "ElementHandle.click:",
        #     "Failed to find element",
        #     "Evaluation failed",
        #     "FAILED",
        #     "failed"
        # ]
        
        # has_error = any(pattern in process.stdout or pattern in process.stderr 
        #                for pattern in error_patterns)
        
        if process.returncode != 0:
            error_output = process.stderr if process.stderr else process.stdout
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
            print("\n=== Success ===")
            print("Script executed without errors")
            print("=============\n")
            state["messages"].append(
                {"role": "system", "content": "Script executed successfully"}
            )
        
        modified_script_content = script_content.replace(
            "(headless=True)", '(headless=False, channel="chrome")'
        ).replace(
            "(headless=False)", '(headless=False, channel="chrome")'
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as chrome_f:
            chrome_f.write(modified_script_content)
            chrome_temp_path = chrome_f.name

        print("\n=== Modified Script for Chrome Execution ===")
        print(modified_script_content)
        print("=====================\n")

        print("\nRunning Playwright test in Chrome for stability check (Headless=False)...")
        chrome_process = subprocess.run(["python", chrome_temp_path], capture_output=True, text=True)

        if chrome_process.returncode != 0:
            print("\nChrome Stability Test Failed:")
            print("==================================\n")
            print(chrome_process.stderr)
            state["messages"].append({"role": "system", "content": "Chrome execution failed, marking as unstable."})
            state["stability_check_passed"] = False
        else:
            print("\nChrome Execution Passed! Test is stable.")
            print("==================================\n")
            state["messages"].append({"role": "system", "content": "Chrome execution passed, test is stable."})
            state["stability_check_passed"] = True
        
        state["has_errors"] = False

    finally:
        os.unlink(temp_path)
        os.unlink(chrome_temp_path)
    return state


def handle_errors(state):
    return "retry" if state.get("has_errors", False) else "success"


def retry_with_errors(state, llm, error_prompt):
    print("\n=== Retrying with error ===")
    print(f"Error message: {state['error_message']}")
    print("========================\n")

    prompt = error_prompt.invoke(
        {
            "original_script": state["messages"][-2].content,
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
    }


def clear_memory(state):
    return {
        **state,
        "messages": [],
        "has_errors": False,
        "error_message": None,
        "execution_time": None,
        "success_rate": None,
        "error_rate": None,
        "retry_count": None
    }
