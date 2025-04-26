import os
import tempfile
import subprocess
import platform
import re
import shutil
import json
from langgraph.types import StreamWriter
from agent.utils.get_html import clean_html, extract_automation_elements, optimize_html_for_llm
from shared_utils.jira import add_comment_to_jira, move_ticket_to_next_status
from .builders import get_script_builder
from shared_utils.job_control import job_cancellation_flags


# Function to execute the current step script
def execute_step_script(state, writer: StreamWriter):
    """Execute Playwright Python script"""
    if job_cancellation_flags.get("current_job"):
        writer({"type": "info", "message": "Test generation cancelled"})
        return {**state, "stop_execution": True}
    
    script_builder = get_script_builder()
    if not script_builder:
        writer({"type": "error", "message": "Script builder not initialized"})
        state["has_errors"] = True
        state["error_message"] = "Script builder not initialized"
        return state
        
    try:
        step_script = script_builder.render_script()
        script_content = state["messages"][-1].content
        writer({"type": "info", "message": f"Executing step {state['current_step_index'] + 1}: {state['current_step']}"})
        print(f"script_content: {script_content}")

        print(f"step_script: {step_script}")
        # Write the script to a temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(step_script)
            temp_path = f.name
        
        # Execute the script
        try:
            # Run the script with pytest
            result = subprocess.run(
                ["pytest", temp_path, "-v"],
                capture_output=True,
                text=True,
                check=False
            )
            
            # Check if the script executed successfully
            if result.returncode == 0:
                writer({"type": "success", "message": f"Step {state['current_step_index'] + 1} executed successfully"})
                # writer({"type": "success", "message": "Tests executed successfully"})
                writer({"type": "script", "message": step_script})
                
                if state["current_step_index"] + 1 == len(state["steps_list"]):
                    writer({"type": "success", "message": "Tests executed successfully"})
                # rag_manager.store_test_result(
                #     framework="playwright",
                #     test_script=step_script,
                #     test_steps=state["current_step"],  # Store just the current step description
                #     html_content=state["html_content"],
                #     success=True,
                #     metadata={
                #         "is_complete_script": False,
                #         "step_number": state["current_step_index"] + 1,
                #         "total_steps": len(state["steps_list"]),
                #         "step_description": state["current_step"]
                #     }
                # )

                with open('latest_page.html', 'r', encoding='utf-8') as f:
                    html = f.read()
                    
                    if html:
                        latest_html = clean_html(html)
                        latest_html = extract_automation_elements(latest_html)
                        latest_html = optimize_html_for_llm(latest_html)
                        
                        with open('latest_html_output.html', 'w', encoding='utf-8') as html_file:
                            html_file.write(latest_html)

                # If this was the last step, send Jira success message and move ticket
                if state["current_step_index"] + 1 == len(state["steps_list"]):
                    jira_id = state.get("jira_ticket_id")
                    if isinstance(jira_id, str) and "SCRUM-" in jira_id:
                        try:
                            add_comment_to_jira(state["jira_ticket_id"], "✅ Test script passed successfully via ArchiTest.", state["jira_email"], state["jira_token"], state["jira_domain"])
                            move_ticket_to_next_status(state["jira_ticket_id"], state["jira_email"], state["jira_token"], state["jira_domain"])
                        except Exception as e:
                            print(f"Jira update failed: {str(e)}")
                            
                return {
                    "html_content": latest_html,
                    "has_errors": False,
                    "error_message": None,
                    "completed_steps": state["completed_steps"] + [state["current_step"]],
                    "current_step_index": state["current_step_index"] + 1,
                    "current_step": state["steps_list"][state["current_step_index"] + 1] if state["current_step_index"] + 1 < len(state["steps_list"]) else None,
                    "accumulated_script": step_script,
                }
            else:
                # rag_manager.store_test_result(
                #     framework="playwright",
                #     test_script=step_script,
                #     test_steps=state["current_step"],  # Store just the current step description
                #     html_content=state["html_content"],
                #     success=False,
                #     error_message=error_message,
                #     metadata={
                #         "is_complete_script": False,
                #         "step_number": state["current_step_index"] + 1,
                #         "total_steps": len(state["steps_list"]),
                #         "step_description": state["current_step"]
                #     }
                # )
                error_message = result.stderr if result.stderr else result.stdout
                writer({"type": "error", "message": f"Step {state['current_step_index'] + 1} failed", "errors": error_message})
                writer({"type": "error", "message": "Test execution failed", "errors": error_message})
                writer({"type": "script", "message": step_script})
                
                
                return {
                    # "retry_count": state.get("retry_count", 0),
                    "has_errors": True,
                    "error_message": error_message,
                }

        except Exception as e:
            writer({"type": "error", "message": f"Error executing step {state['current_step_index'] + 1}: {str(e)}"})
            return state
        finally:
            # Clean up the temporary file
            try:
                os.unlink(temp_path)
            except:
                pass
    except Exception as e:
        writer({"type": "error", "message": f"Failed to render script: {str(e)}"})
        state["has_errors"] = True
        state["error_message"] = str(e)
        return state

def execute_selenium_script(state, writer: StreamWriter):
    """Execute Java Selenium script with enhanced HTML capture and step-by-step execution"""
    print("inside execute_selenium_script")
    if job_cancellation_flags.get("current_job"):
        writer({"type": "info", "message": "Test generation cancelled"})
        return {**state, "stop_execution": True}
        
    script_builder = get_script_builder()
    step_script = script_builder.render_script()
    script_content = state["messages"][-1].content
    writer({"type": "info", "message": f"Executing step {state['current_step_index'] + 1}: {state['current_step']}"})

    print(f"step_script: {step_script}")
    state["last_script"] = step_script

    match = re.search(r'public\s+class\s+(\w+)', step_script)
    if not match:
        writer({"type": "error", "message": "Could not find a public class in the script."})
        state["has_errors"] = True
        return state
    class_name = match.group(1)

    with tempfile.TemporaryDirectory() as tmpdir:
        # Add file to save HTML content to
        html_output_file = os.path.join(tmpdir, "latest_page.html")
        
        # Insert code to capture HTML to the script
        modified_script = step_script.replace(
            "driver.quit();", 
            f"""
            // Capture HTML for analysis before quitting
            try {{
                String html = (String) ((org.openqa.selenium.JavascriptExecutor) driver).executeScript("return document.documentElement.outerHTML");
                java.nio.file.Files.write(java.nio.file.Paths.get("{html_output_file.replace('\\', '\\\\')}"), html.getBytes());
            }} catch (Exception e) {{
                System.err.println("Error capturing HTML: " + e.getMessage());
            }}
            driver.quit();
            """
        )
        
        java_file_path = os.path.join(tmpdir, f"{class_name}.java")
        with open(java_file_path, "w") as f:
            f.write(modified_script)

        writer({"type": "info", "message": "Executing Java Selenium test script"})

        # Get the path to the project root
        SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))  # nodes folder
        UTILS_DIR = os.path.dirname(SCRIPT_DIR)  # utils folder
        AGENT_DIR = os.path.dirname(UTILS_DIR)  # agent folder
        JAVA_UTILS_DIR = os.path.join(AGENT_DIR, "utils", "java_utils")

        # Verify Java utils directory exists
        if not os.path.exists(JAVA_UTILS_DIR):
            writer({"type": "error", "message": f"Java utils directory not found at {JAVA_UTILS_DIR}"})
            state["has_errors"] = True
            state["error_message"] = "Java utils directory not found"
            return state

        # Setup paths for Selenium and ChromeDriver
        selenium_jar_path = os.path.join(JAVA_UTILS_DIR, "selenium-java-4", "*")
        chromedriver_path = os.path.join(JAVA_UTILS_DIR, "chromedriver-mac-x64", "chromedriver")
        
        # Verify required files exist
        if not os.path.exists(os.path.dirname(selenium_jar_path)):
            writer({"type": "error", "message": "Selenium JAR not found"})
            state["has_errors"] = True
            state["error_message"] = f"Selenium JAR not found at {selenium_jar_path}"
            return state
            
        if not os.path.exists(chromedriver_path):
            writer({"type": "error", "message": "ChromeDriver not found"})
            state["has_errors"] = True
            state["error_message"] = f"ChromeDriver not found at {chromedriver_path}"
            return state

        os.environ["webdriver.chrome.driver"] = chromedriver_path

        sep = ";" if platform.system() == "Windows" else ":"
        classpath = f"{selenium_jar_path}{sep}{tmpdir}"

        compile_command = ["javac", "-cp", classpath, "-d", tmpdir, java_file_path]
        compile_process = subprocess.run(compile_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if compile_process.returncode != 0:
            writer({"type": "error", "message": "Compilation failed", "errors": compile_process.stderr})
            state["messages"].append({"role": "system", "content": f"Compilation failed: {compile_process.stderr}"})
            state["has_errors"] = True
            state["error_message"] = compile_process.stderr
            return state

        run_command = ["java", "-cp", classpath, class_name]
        run_process = subprocess.run(run_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if run_process.returncode != 0:
            writer({"type": "error", "message": "Execution failed", "errors": run_process.stderr})
            writer({"type": "error", "message": "Test execution failed", "errors": run_process.stderr})
            writer({"type": "script", "message": step_script})
            state["messages"].append({"role": "system", "content": f"Execution failed: {run_process.stderr}"})
            state["has_errors"] = True
            state["error_message"] = run_process.stderr
            return state
        else:
            writer({"type": "success", "message": f"Step {state['current_step_index'] + 1} executed successfully"})
            writer({"type": "script", "message": step_script})
            
            # Process the captured HTML if available
            latest_html = None
            if os.path.exists(html_output_file):
                try:
                    with open(html_output_file, 'r', encoding='utf-8') as f:
                        html = f.read()
                        
                    if html:
                        latest_html = clean_html(html)
                        latest_html = extract_automation_elements(latest_html)
                        latest_html = optimize_html_for_llm(latest_html)
                        
                        with open('latest_html_output.html', 'w', encoding='utf-8') as html_file:
                            html_file.write(latest_html)
                except Exception as e:
                    writer({"type": "warning", "message": f"Error processing HTML: {str(e)}"})
            
            # If this is the last step, mark as complete
            if state["current_step_index"] + 1 == len(state["steps_list"]):
                writer({"type": "success", "message": "Tests executed successfully"})
                
                # Handle Jira integration if applicable
                jira_id = state.get("jira_ticket_id")
                if isinstance(jira_id, str) and "SCRUM-" in jira_id:
                    try:
                        add_comment_to_jira(state["jira_ticket_id"], "✅ Test script passed successfully via ArchiTest.", state["jira_email"], state["jira_token"], state["jira_domain"])
                        move_ticket_to_next_status(state["jira_ticket_id"], state["jira_email"], state["jira_token"], state["jira_domain"])
                    except Exception as e:
                        print(f"Jira update failed: {str(e)}")
                
            return {
                "html_content": latest_html if latest_html else state.get("html_content"),
                "has_errors": False,
                "error_message": None,
                "completed_steps": state["completed_steps"] + [state["current_step"]],
                "current_step_index": state["current_step_index"] + 1,
                "current_step": state["steps_list"][state["current_step_index"] + 1] if state["current_step_index"] + 1 < len(state["steps_list"]) else None,
                "accumulated_script": step_script,
            }

def execute_playwright_js_script(state, writer: StreamWriter):
    """Execute JavaScript Playwright script with enhanced HTML capture and step-by-step execution"""
    print("inside execute_playwright_js_script")
    if job_cancellation_flags.get("current_job"):
        writer({"type": "info", "message": "Test generation cancelled"})
        return {**state, "stop_execution": True}
    
    script_builder = get_script_builder()
    step_script = script_builder.render_script()
    script_content = state["messages"][-1].content
    writer({"type": "info", "message": f"Executing step {state['current_step_index'] + 1}: {state['current_step']}"})
    
    print(f"step_script: {step_script}")
    state["last_script"] = step_script

    # Fix path to javascript_utils
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))  # nodes folder
    UTILS_DIR = os.path.dirname(SCRIPT_DIR)  # utils folder
    AGENT_DIR = os.path.dirname(UTILS_DIR)  # agent folder
    JS_UTILS_DIR = os.path.join(AGENT_DIR, "utils", "javascript_utils")

    os.makedirs(JS_UTILS_DIR, exist_ok=True)

    # Check for playwright installation
    if not os.path.exists(os.path.join(JS_UTILS_DIR, "node_modules", "@playwright")):
        error_message = (
            "Playwright module not found. Please run the following commands in "
            f"{JS_UTILS_DIR}:\n"
            "npm init -y\n"
            "npm install -D @playwright/test\n"
            "npx playwright install"
        )
        writer({
            "type": "error",
            "message": error_message
        })
        state["has_errors"] = True
        state["error_message"] = error_message
        return state

    # Add code to capture HTML content after execution
    modified_script = step_script.replace(
        "});", 
        """
    // Capture HTML for analysis
    await page.waitForLoadState('load');
    const html = await page.content();
    const fs = require('fs');
    fs.writeFileSync('latest_page.html', html);
});"""
    )

    with tempfile.NamedTemporaryFile(mode="w", suffix=".spec.js", delete=False, dir=".") as f:
        f.write(modified_script)
        temp_path = f.name

    filename = os.path.basename(temp_path)
    new_script_path = os.path.join(JS_UTILS_DIR, filename)
    shutil.move(temp_path, new_script_path)

    try:
        writer({"type": "info", "message": "Executing JavaScript Playwright test script"})

        process = subprocess.run(
            ["npx", "playwright", "test", filename],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=JS_UTILS_DIR,
            text=True,
        )

        if process.returncode != 0:
            error_output = process.stderr if process.stderr else process.stdout
            writer({"type": "error", "message": "Test execution failed", "errors": error_output})
            writer({"type": "script", "message": step_script})
            state["messages"].append({"role": "system", "content": f"Script execution failed: {error_output}"})
            state["has_errors"] = True
            state["error_message"] = error_output
            return state
        else:
            writer({"type": "success", "message": f"Step {state['current_step_index'] + 1} executed successfully"})
            writer({"type": "script", "message": step_script})
            
            # Process HTML content if available
            latest_html = None
            html_file_path = os.path.join(JS_UTILS_DIR, 'latest_page.html')
            if os.path.exists(html_file_path):
                try:
                    with open(html_file_path, 'r', encoding='utf-8') as f:
                        html = f.read()
                        
                    if html:
                        latest_html = clean_html(html)
                        latest_html = extract_automation_elements(latest_html)
                        latest_html = optimize_html_for_llm(latest_html)
                        
                        with open('latest_html_output.html', 'w', encoding='utf-8') as html_file:
                            html_file.write(latest_html)
                except Exception as e:
                    writer({"type": "warning", "message": f"Error processing HTML: {str(e)}"})
                    
            # If this is the last step, mark as complete
            if state["current_step_index"] + 1 == len(state["steps_list"]):
                writer({"type": "success", "message": "Tests executed successfully"})
                
                # Handle Jira integration if applicable
                jira_id = state.get("jira_ticket_id")
                if isinstance(jira_id, str) and "SCRUM-" in jira_id:
                    try:
                        add_comment_to_jira(state["jira_ticket_id"], "✅ Test script passed successfully via ArchiTest.", state["jira_email"], state["jira_token"], state["jira_domain"])
                        move_ticket_to_next_status(state["jira_ticket_id"], state["jira_email"], state["jira_token"], state["jira_domain"])
                    except Exception as e:
                        print(f"Jira update failed: {str(e)}")
            
            return {
                "html_content": latest_html if latest_html else state.get("html_content"),
                "has_errors": False,
                "error_message": None,
                "completed_steps": state["completed_steps"] + [state["current_step"]],
                "current_step_index": state["current_step_index"] + 1,
                "current_step": state["steps_list"][state["current_step_index"] + 1] if state["current_step_index"] + 1 < len(state["steps_list"]) else None,
                "accumulated_script": step_script,
            }
    finally:
        try:
            os.unlink(new_script_path)
        except:
            pass

    return state

def execute_postman_collection(state, writer: StreamWriter):
    """Execute a Postman collection for API testing with improved execution flow."""
    if job_cancellation_flags.get("current_job"):
        writer({"type": "info", "message": "Test generation cancelled"})
        return {**state, "stop_execution": True}
    
    print("inside execute_postman_collection")
    script_content = state["messages"][-1].content
    state["last_script"] = script_content

    writer({"type": "info", "message": "Executing API Test"})
    writer({"type": "script", "message": script_content})

    print("\n=== Generated Script ===")
    print(script_content)
    print("=====================\n")

    # Fix path to javascript_utils
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))  # nodes folder
    UTILS_DIR = os.path.dirname(SCRIPT_DIR)  # utils folder
    AGENT_DIR = os.path.dirname(UTILS_DIR)  # agent folder
    JS_UTILS_DIR = os.path.join(AGENT_DIR, "utils", "javascript_utils")
    NEWMAN_PATH = os.path.join(JS_UTILS_DIR, "node_modules", ".bin", "newman")

    # Create directory if it doesn't exist
    os.makedirs(JS_UTILS_DIR, exist_ok=True)

    # Check for newman installation
    if not os.path.exists(os.path.join(JS_UTILS_DIR, "node_modules", "newman")):
        error_message = (
            "Newman module not found. Please run the following commands in "
            f"{JS_UTILS_DIR}:\n"
            "npm init -y\n"
            "npm install newman"
        )
        writer({
            "type": "error",
            "message": error_message
        })
        state["has_errors"] = True
        state["error_message"] = error_message
        return state

    # Write the collection to a temp file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, dir=".") as f:
        f.write(script_content)
        temp_path = f.name

    filename = os.path.basename(temp_path)
    new_script_path = os.path.join(JS_UTILS_DIR, filename)
    shutil.move(temp_path, new_script_path)

    # Create a file to capture the response data
    response_file_path = os.path.join(JS_UTILS_DIR, "api_response.json")

    try:
        writer({"type": "info", "message": "Executing Postman collection"})
        
        # Run newman (Postman CLI) with JSON reporter to capture response data
        process = subprocess.run(
            [NEWMAN_PATH, "run", filename, "--reporters", "json", "--reporter-json-export", "api_response.json"],
            capture_output=True,
            cwd=JS_UTILS_DIR,
            text=True
        )

        output = process.stdout if process.stdout else process.stderr
        
        # Check for failed assertions in the newman output
        if "failure" in output or process.returncode != 0:
            writer({"type": "error", "message": "API test execution failed", "errors": output})
            state["has_errors"] = True
            state["error_message"] = output
            # Store the specific assertion errors for better retry context
            if "AssertionError" in output:
                state["assertion_errors"] = [line for line in output.split('\n') if "AssertionError" in line]
            return state
        else:
            writer({"type": "success", "message": "API tests executed successfully"})
            
            # Try to extract the API response data
            if os.path.exists(os.path.join(JS_UTILS_DIR, "api_response.json")):
                try:
                    with open(os.path.join(JS_UTILS_DIR, "api_response.json"), 'r') as f:
                        response_data = json.load(f)
                        
                    # Extract API responses for future steps
                    api_results = {}
                    if "run" in response_data and "executions" in response_data["run"]:
                        for execution in response_data["run"]["executions"]:
                            if "response" in execution and "stream" in execution["response"]:
                                req_name = execution.get("item", {}).get("name", "unknown_request")
                                try:
                                    # Attempt to extract and parse JSON response data
                                    stream_data = execution["response"]["stream"]["data"]
                                    api_results[req_name] = json.loads(stream_data)
                                except Exception:
                                    api_results[req_name] = "Non-JSON response"
                                    
                    state["api_results"] = api_results
                except Exception as e:
                    writer({"type": "warning", "message": f"Error processing API response: {str(e)}"})
            
            return {
                "completed_steps": [state["current_step"]],  # All steps completed
                "current_step_index": 1,  # Mark as completed
                "current_step": None,  # No more steps
                "has_errors": False,
                "accumulated_script": script_content,
                "api_results": state.get("api_results", {})
            }

    finally:
        os.unlink(new_script_path)
        # Also clean up the response file
        try:
            if os.path.exists(os.path.join(JS_UTILS_DIR, "api_response.json")):
                os.unlink(os.path.join(JS_UTILS_DIR, "api_response.json"))
        except:
            pass
    
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
        chrome_process = subprocess.run(["python", "-m", "pytest", chrome_temp_path], capture_output=True, text=True)

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

__all__ = [
    'execute_step_script',
    'execute_selenium_script',
    'execute_playwright_js_script',
    'execute_postman_collection',
    'execute_chrome_script'
]