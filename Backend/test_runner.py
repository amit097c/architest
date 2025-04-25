import asyncio
import json
import os
import subprocess
import tempfile
import traceback
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

router = APIRouter()

class TestRunRequest(BaseModel):
    id: str
    name: str
    framework: str
    language: str
    testScript: str
    url: str

class TestRunResult(BaseModel):
    id: str
    status: str
    output: List[str]
    execution_time: float

# Cache of running test processes
active_tests = {}

@router.post("/api/run-test", response_model=Dict)
async def run_test(test_request: TestRunRequest):
    """
    Run a test with the specified framework and return results
    """
    try:
        test_id = test_request.id
        script = test_request.testScript
        
        # Check if test is already running
        if test_id in active_tests:
            return {"error": "Test is already running", "id": test_id}
        
        # Write the script to a temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(script)
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
                print("success")
            else:
                print("fail")
        except Exception as e:
            print("error")
        finally:
            # Clean up the temporary file
            try:
                os.unlink(temp_path)
            except:
                pass
        
        return {
            "id": test_id,
            "status": "running"
        }
        
    except Exception as e:
        print(f"Error starting test: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/test-status/{test_id}", response_model=Dict)

async def get_test_status(test_id: str):
    """
    Get the status and output of a running or completed test
    """
    if test_id not in active_tests:
        raise HTTPException(status_code=404, detail="Test not found")
    
    test_info = active_tests[test_id]
    current_time = asyncio.get_event_loop().time()
    execution_time = current_time - test_info["start_time"]
    
    # Check if test has completed
    if test_info["status"] in ["passed", "failed"]:
        result = {
            "id": test_id,
            "status": test_info["status"],
            "output": test_info["output"],
            "execution_time": execution_time
        }
        
        # Clean up completed tests after a while
        if execution_time > 60:  # Remove after 1 minute
            cleanup_test(test_id)
            
        return result
    
    # Test is still running
    return {
        "id": test_id,
        "status": "running",
        "output": test_info["output"],
        "execution_time": execution_time
    }

@router.delete("/api/cancel-test/{test_id}", response_model=Dict)
async def cancel_test(test_id: str):
    """
    Cancel a running test
    """
    if test_id not in active_tests:
        raise HTTPException(status_code=404, detail="Test not found")
    
    # Terminate the process
    try:
        active_tests[test_id]["process"].terminate()
        active_tests[test_id]["status"] = "cancelled"
        cleanup_test(test_id)
        return {"success": True, "id": test_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def cleanup_test(test_id: str):
    """Clean up test resources"""
    if test_id in active_tests:
        # Clean up any temporary files
        try:
            if "test_file" in active_tests[test_id] and os.path.exists(active_tests[test_id]["test_file"]):
                os.remove(active_tests[test_id]["test_file"])
        except:
            pass
        
        # Remove from active tests after some time
        current_time = asyncio.get_event_loop().time()
        execution_time = current_time - active_tests[test_id]["start_time"]
        if execution_time > 300:  # Keep in memory for 5 minutes max
            del active_tests[test_id]

async def create_test_file(test_request: TestRunRequest) -> str:
    """Create a test file from template or from scratch"""
    try:
        # Determine file extension based on language
        extensions = {
            "python": ".py",
            "javascript": ".js",
            "typescript": ".ts"
        }
        
        ext = extensions.get(test_request.language, ".py")
        
        # Create temp file with proper extension
        fd, path = tempfile.mkstemp(suffix=ext)
        
        # Check if we should use a template
        if not test_request.test_script.strip():
            # Use template based on framework and language
            template_content = get_template_content(test_request.framework, test_request.language)
            
            # Replace placeholders
            template_content = template_content.replace("{{TEST_URL}}", test_request.url)
            template_content = template_content.replace("{{TEST_NAME}}", test_request.name)
            template_content = template_content.replace("{{TEST_STEPS}}", "# Add your test steps here")
            
            with os.fdopen(fd, 'w') as tmp:
                tmp.write(template_content)
        else:
            # Use the provided test script
            with os.fdopen(fd, 'w') as tmp:
                tmp.write(test_request.test_script)
        
        return path
    except Exception as e:
        print(f"Error creating test file: {str(e)}")
        raise e

def get_template_content(framework: str, language: str) -> str:
    """Get the content of a template file"""
    templates_dir = os.path.join(os.path.dirname(__file__), "templates")
    
    if framework == "playwright" and language == "python":
        template_path = os.path.join(templates_dir, "playwright_template.py")
    elif framework == "cypress":
        template_path = os.path.join(templates_dir, "cypress_template.js")
    elif framework == "selenium" and language == "python":
        template_path = os.path.join(templates_dir, "selenium_template.py")
    else:
        # Default to a simple template
        return f"""
        # Test for {framework} in {language}
        # URL: {{{{TEST_URL}}}}
        # Please add your test code here.
        """
    
    # Read the template file
    if os.path.exists(template_path):
        with open(template_path, 'r') as f:
            return f.read()
    else:
        return f"# Template not found for {framework} in {language}\n# URL: {{{{TEST_URL}}}}"

def start_test_process(test_request: TestRunRequest, test_file_path: str):
    """Start the appropriate test process based on framework and language"""
    try:
        cmd = []
        
        if test_request.framework == "playwright":
            if test_request.language == "python":
                cmd = ["python", "-m", "playwright", "test", test_file_path]
            elif test_request.language in ["javascript", "typescript"]:
                cmd = ["npx", "playwright", "test", test_file_path]
        
        elif test_request.framework == "cypress":
            cmd = ["npx", "cypress", "run", "--spec", test_file_path]
        
        elif test_request.framework == "selenium":
            if test_request.language == "python":
                cmd = ["python", test_file_path]
            elif test_request.language in ["javascript", "typescript"]:
                cmd = ["node", test_file_path]
        
        if not cmd:
            raise ValueError(f"Unsupported framework/language: {test_request.framework}/{test_request.language}")
        
        # Start the process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        return process
    except Exception as e:
        print(f"Error starting process: {str(e)}")
        raise e

async def collect_output(test_id: str, process):
    """Collect output from the process and update the test status"""
    try:
        for line in iter(process.stdout.readline, ""):
            if not line:
                break
                
            # Add to output buffer
            active_tests[test_id]["output"].append(line.strip())
            
            # Check for potential test status indicators in pytest output
            line_lower = line.lower()
            if "failed" in line_lower or "error" in line_lower:
                active_tests[test_id]["status"] = "failed"
            elif "passed" in line_lower or "success" in line_lower:
                active_tests[test_id]["status"] = "passed"
        
        # Wait for process to complete
        return_code = process.wait()
        
        # Set final status based on return code if not already set
        if active_tests[test_id]["status"] == "running":
            active_tests[test_id]["status"] = "passed" if return_code == 0 else "failed"
            
    except Exception as e:
        print(f"Error collecting output: {str(e)}")
        active_tests[test_id]["status"] = "failed"
        active_tests[test_id]["output"].append(f"Error in test runner: {str(e)}") 