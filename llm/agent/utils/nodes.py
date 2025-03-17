import tempfile
import subprocess
import os
from agent.utils.tools import clean_script_response
from langgraph.types import StreamWriter

# Function defined to invoke the LLM model with its configuration
def invoke_llm(state, llm, prompt_template, writer: StreamWriter):
    # For sending Generating Script message to the frontend
    writer({"type": "info", "message": "Generating script"})
    
    prompt = prompt_template.invoke(
        {
            "test_steps": state["test_steps"],
            "html_content": state["html_content"],
            "url": state["url"],
            "messages": state["messages"],
        }
    )
    response = llm.invoke(prompt)
    # get the response and clean it to remove the markdown syntax
    cleaned_content = clean_script_response(response.content)
    # return the cleaned content
    return {"messages": [{"role": "assistant", "content": cleaned_content}]}

# Function defined to execute the Playwright script
def execute_playwright_script(state, writer: StreamWriter):
    # Get the last message from the state
    script_content = state["messages"][-1].content
    print("\n=== Generated Script ===")
    print(script_content)
    print("=====================\n")

    # Write the script to a temporary file with its wrapper depending on the script type
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
        # subprocess.run(["pip", "install", "playwright"], check=True, capture_output=True)
        # subprocess.run(["playwright", "install", "chromium"], check=True, capture_output=True)
        
        writer({"type": "info", "message": "Executing test script"})
        
        # Run the script with shell=True to ensure proper execution
        process = subprocess.run(
            f"pytest {temp_path}", 
            shell=True,
            capture_output=True,
            text=True,
            env=os.environ.copy()  # Pass current environment
        )
        
        # Check if the process returned an error
        if process.returncode != 0:
            # Get the error output from the process
            error_output = process.stderr if process.stderr else process.stdout
            
            # Send the error message to the frontend
            writer({"type": "error", "message": "Test execution failed"})
            
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
        # If the process returned successfully
        else:
            # Send the success message to the frontend
            writer({"type": "success", "message": "Tests executed successfully"})
            # Send the script content to the frontend
            writer({"type": "script", "message": script_content})
            print("\n=== Success ===")
            print("Script executed without errors")
            print("=============\n")
            state["messages"].append(
                {"role": "system", "content": "Script executed successfully"}
            )
        #chrome_stability_test(script_content,state)

            # For executing the script in chrome for Chrome test stability check
            stability_check, stability_message = execute_chrome_script(script_content)
            state["messages"].append({"role": "system", "content": stability_message})
            state["stability_check_passed"] = stability_check
            state["has_errors"] = False
                    
    finally:
        # Remove the temporary file after it finish everything
        os.unlink(temp_path)
    return state

# Function defined to execute the Playwright script in Chrome for chrome stability check
def execute_chrome_script(script_content):
    """Executes the given Playwright script in Chrome with headless mode off."""
    # Modify the script content to run in Chrome with headless mode off
    modified_script_content = script_content.replace(
        "(headless=True)", '(headless=True, channel="chrome")'
    ).replace(
        "(headless=False)", '(headless=True, channel="chrome")'
    )

    # Write the modified script to a temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as chrome_f:
        chrome_f.write(modified_script_content)
        chrome_temp_path = chrome_f.name
    
    try:
        print("Running Playwright test in Chrome for stability check (Headless=False)...")
        # Run the script with shell=True to ensure proper execution
        chrome_process = subprocess.run(["python", chrome_temp_path], capture_output=True, text=True)

        # Check if the process returned an error
        if chrome_process.returncode != 0:
            print("Chrome Stability Test Failed, Test is unstable due to :\n%s", chrome_process.stderr)
            return False, chrome_process.stderr
        else:
            # If the process returned successfully
            print("Chrome Execution Passed! Test is stable.")
            return True, "Chrome execution passed."
    finally:
        # Remove the temporary file after it finish everything
        os.unlink(chrome_temp_path)

# Function defined to handle errors
def handle_errors(state):
    return "retry" if state.get("has_errors", False) else "success"

# Function defined to send a custom prompt to the LLM model if the script execution fails
def retry_with_errors(state, llm, error_prompt, writer: StreamWriter):
    # Send the message to the frontend
    writer({"type": "info", "message": "Refining test script"})
    
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

    # Invoke the LLM model with the custom prompt
    response = llm.invoke(prompt)
    # get the response and clean it to remove the markdown syntax
    cleaned_content = clean_script_response(response.content)

    # Return the cleaned content and its state
    return {
        **state,
        "messages": [{"role": "assistant", "content": cleaned_content}],
        "has_errors": False,
        "error_message": None,
    }

# Function defined to clear the memory after a succesful script execution
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
