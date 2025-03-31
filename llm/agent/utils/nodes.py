import tempfile
import subprocess
import os
from agent.utils.tools import clean_script_response
from langgraph.types import StreamWriter
import platform
import re
import shutil

# Function defined to invoke the LLM model with its configuration
def invoke_llm(state, llm, prompt_template_playwright, prompt_template_selenium, prompt_template_playwright_js, writer: StreamWriter):
    writer({"type": "info", "message": "Generating script"})
    
    framework = state["framework"]
    language = state["language"]
    
    if framework == "playwright":
        # Choose prompt based on language
        if language == "javascript":
            prompt = prompt_template_playwright_js.invoke({
                "test_steps": state["test_steps"],
                "html_content": state["html_content"],
                "url": state["url"],
                "messages": state["messages"],
            })
        else:  # python
            prompt = prompt_template_playwright.invoke({
                "test_steps": state["test_steps"],
                "html_content": state["html_content"],
                "url": state["url"],
                "messages": state["messages"],
            })
    
    elif framework == "selenium":
        # Selenium only supports Java for now
        prompt = prompt_template_selenium.invoke({
            "test_steps": state["test_steps"],
            "html_content": state["html_content"],
            "url": state["url"],
            "messages": state["messages"],
        })
    
    response = llm.invoke(prompt)
    cleaned_content = clean_script_response(response.content)
    print(f"generated {framework} {language} script: {cleaned_content}")
    
    return {"messages": [{"role": "assistant", "content": cleaned_content}]}

# Function defined to execute the Playwright script
def execute_playwright_script(state, writer: StreamWriter):
    # Get the last message from the state
    print("inside execute_playwright_script")
    script_content = state["messages"][-1].content
    state["last_script"] = script_content
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
        #f.write(script_content)
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
            writer({"type": "error", "message": "Test execution failed", "errors": error_output})
            writer({"type": "script", "message": state["last_script"]})
            
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
            writer({"type": "script", "message": state["last_script"]})
            print("\n=== Success ===")
            print("Script executed without errors")
            print("=============\n")
            state["messages"].append(
                {"role": "system", "content": "Script executed successfully"}
            )
        #chrome_stability_test(script_content,state)

            # For executing the script in chrome for Chrome test stability check
            stability_check, stability_message = execute_chrome_script(state["last_script"])
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


def execute_selenium_script(state, writer: StreamWriter):
    # Get the last message from the state
    print("inside execute_selenium_script")
    script_content = state["messages"][-1].content
    state["last_script"] = script_content
    print("\n=== Generated Script (JAVA) ===")
    print(script_content)
    print("=====================\n")

    match = re.search(r'public\s+class\s+(\w+)', script_content)
    if not match:
        writer({"type": "error", "message": "Could not find a public class in the script."})
        return
    class_name = match.group(1)

    with tempfile.TemporaryDirectory() as tmpdir:
        java_file_path = os.path.join(tmpdir, f"{class_name}.java")
        with open(java_file_path, "w") as f:
            f.write(script_content)

    # try:
        writer({"type": "info", "message": "Executing test script"})
        
        # Get the current script's directory (i.e., utils/)
        SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

        # Define the relative path to java_utils/
        JAVA_UTILS_DIR = os.path.join(SCRIPT_DIR, "java_utils")

        # paths
        selenium_jar_path = os.path.join(JAVA_UTILS_DIR, "selenium-java-4", "*")  # Path to the Selenium JARs
        chromedriver_path = os.path.join(JAVA_UTILS_DIR, "chromedriver-mac-x64", "chromedriver")  # Path to ChromeDriver

        os.environ["webdriver.chrome.driver"] = chromedriver_path

        sep = ";" if platform.system() == "Windows" else ":"

        classpath = f"{selenium_jar_path}{sep}{tmpdir}"

       # Command to run the Java test automation script
       # Compile the Java file
        compile_command = [
            "javac",
            "-cp", classpath,
            "-d", tmpdir,
            java_file_path
        ]
        compile_process = subprocess.run(compile_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if compile_process.returncode != 0:
            print("Compilation failed:", compile_process.stderr)
            writer({"type": "error", "message": "Compilation failed", "errors": compile_process.stderr})
            writer({"type": "script", "message": state["last_script"]})
            state["messages"].append({"role": "system", "content": f"Script compilation failed: {compile_process.stderr}"})
            state["has_errors"] = True
            state["error_message"] = compile_process.stderr
            return state

        # Run the compiled class
        class_name = os.path.basename(java_file_path).replace(".java", "")
        run_command = [
            "java",
            "-cp", classpath,
            class_name
        ]
        run_process = subprocess.run(run_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if run_process.returncode != 0:
            print("Execution failed:", run_process.stderr)
            writer({"type": "error", "message": "Execution failed", "errors": run_process.stderr})
            writer({"type": "script", "message": state["last_script"]})
            state["messages"].append({"role": "system", "content": f"Script execution failed: {run_process.stderr}"})
            state["has_errors"] = True
            state["error_message"] = run_process.stderr
        else:
            print("Execution Output:", run_process.stdout)
            writer({"type": "success", "message": "Tests executed successfully"})
            writer({"type": "script", "message": state["last_script"]})
            state["messages"].append({"role": "system", "content": "Script executed successfully"})
            state["has_errors"] = False
    return state

# Function to execute javascript code
def execute_playwright_js_script(state, writer: StreamWriter):
    print("inside execute_playwright_js_script")
    script_content = state["messages"][-1].content
    state["last_script"] = script_content
    language = state.get("language", "javascript")
    print(f"\n=== Generated Script ({language.upper()}) ===")
    print(script_content)
    print("=====================\n")

    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    JS_UTILS_DIR = os.path.join(SCRIPT_DIR, "javascript_utils")

    # Ensure directory exists
    os.makedirs(JS_UTILS_DIR, exist_ok=True)

    if not os.path.exists(os.path.join(JS_UTILS_DIR, "node_modules", "playwright")):
        writer({
            "type": "error",
            "message": "Playwright module not found. Please run `npm install` inside javascript_utils directory."
        })
        state["has_errors"] = True
        return state

    """Execute a JavaScript Playwright test script."""
    # Write the script to a temporary JavaScript file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".spec.js", delete=False, dir=".") as f:
        f.write(script_content)
        temp_path = f.name

    filename = os.path.basename(temp_path)
    new_script_path = os.path.join(JS_UTILS_DIR, filename)
    shutil.move(temp_path, new_script_path)
    
    try:
        writer({"type": "info", "message": "Executing JavaScript test script"})
        print(f"\nRunning Playwright test: npx playwright test {filename}")
        print(f"CWD: {JS_UTILS_DIR}")
        print("=====================\n")
        
        # Run the script using Node.js
        process = subprocess.run(
            ["npx", "playwright", "test", filename],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=JS_UTILS_DIR,
            text=True,
        )
        
        # Check if the process returned an error
        if process.returncode != 0:
            # error_output = process.stderr.strip() or process.stdout.strip()
            error_output = process.stderr if process.stderr else process.stdout
            
            writer({"type": "error", "message": "Test execution failed", "errors": error_output})
            writer({"type": "script", "message": state["last_script"]})
            
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
            writer({"type": "success", "message": "Tests executed successfully"})
            writer({"type": "script", "message": state["last_script"]})
            print("\n=== Success ===")
            print("Script executed without errors")
            print("=============\n")
            state["messages"].append(
                {"role": "system", "content": "Script executed successfully"}
            )
            state["has_errors"] = False
                
    finally:
        os.unlink(new_script_path)
    return state


# Function defined to handle errors
def handle_errors(state):
    return "retry" if state.get("has_errors", False) else "success"

def limit_error(state):
    # Check if the execution should be stopped
    if state.get("stop_execution", False):
        return "stop"
    
    # Determine which framework to use (Playwright or Selenium)
    framework = state.get("framework")
    language = state.get("language")

    if framework == "selenium":
        return "execute_selenium"
    elif framework == "playwright":
        return "execute_playwright_js" if language == "javascript" else "execute_playwright"
    
def handle_framework(state):
    print("inside handle framework")
    if state["framework"] == "playwright" and state["language"] == "python":
        return "execute_playwright_script"
    elif state["framework"] == "playwright" and state["language"] == "javascript":
        return "execute_playwright_js_script"
    elif state["framework"] == "selenium":
        return "execute_selenium_script"

def retry_with_errors(state, llm,  error_prompt_playwright, error_prompt_selenium, error_prompt_playwright_js, writer: StreamWriter):
    state["retry_count"] = state.get("retry_count", 0) + 1

    writer({"type": "info", "message": f"Refining test script (Attempt {state['retry_count']}/10)"})

    if state["retry_count"] >= 10:
        errors = state["messages"][-1].content if state["messages"] else "No script generated."
        writer({
            "type": "error", 
            "message": "Max refinement attempts reached. Please check your test steps and/or the webpage.",
            "details": errors,
            "maxAttempts": True  # Add a flag to identify this specific case
        })

        print("\nMax retries reached. Stopping further refinements.")

        return {
        **state,
        "messages": [{"role": "system", "content": "Test generation failed. Max retries reached."}],
        "stop_execution": True,
        "error_message": "Max retries reached",
        }
    
    else:
        print("\n=== Retrying with error ===")
        print(f"Error message: {state['error_message']}")
        print("========================\n")
        original_script = state.get("last_script", "")

        if state["framework"] == "playwright" and state["language"] == "python":
            print("inside playwright retry")
            prompt = error_prompt_playwright.invoke(
                    {
                        "original_script": original_script,
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
        elif state["framework"] == "playwright" and state["language"] == "javascript":
            print("inside playwright js retry")
            prompt = error_prompt_playwright_js.invoke(
                    {
                        "original_script": original_script,
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
        elif state["framework"] == "selenium":
            print("inside selenium retry")
            prompt = error_prompt_selenium.invoke(
                    {
                        "original_script": original_script,
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
