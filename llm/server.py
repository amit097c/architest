import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
import json
import asyncio
from agent.agent import step_graph
from typing import Optional, List
from shared_utils.job_control import job_cancellation_flags

app = FastAPI()

# Global queue to hold the streaming data
data_queue = asyncio.Queue()


# Define the request body model using Pydantic
class PromptReq(BaseModel):
    prompt: str


@app.post("/generate_tests")
async def generate_tests(request: Request):
    try:
        data = await request.json()
        # Set default values for API tests
        if data.get("is_api_test", False):
            if not data.get("url"):
                data["url"] = [data.get("api_details", {}).get("endpoint", "")]
            if not data.get("language"):
                data["language"] = data.get("framework")  # Use framework as language for API tests
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")

    # Validate required fields
    required_fields = ["url", "test_steps", "html_content", "framework"]
    for field in required_fields:
        if field not in data:
            raise HTTPException(
                status_code=400, detail=f"Missing required field: {field}"
            )

    # Get the generation approach (step-by-step or legacy)
    approach = data.get("approach", "step_by_step")
    
    # Initialize state with required fields
    state_update = {
        "messages": [],
        "url": data.get("url", ""),
        "test_steps": data.get("test_steps", ""),
        "html_content": data.get("html_content", ""),
        "has_errors": False,
        "error_message": None,
        "framework": data.get("framework", "playwright"),
        "language": data.get("language", "python"),  # Python language as default
        "last_script": data.get("last_script", None),
        "max_retries": int(data.get("max_retries", 10)),
        "jira_ticket_id": data.get("jira_ticket_id", None),
        "jira_email": data.get("jira_email", None),
        "jira_token": data.get("jira_token", None),
        "jira_domain": data.get("jira_domain", None),
        "is_api_test": data.get("is_api_test", False),
        "api_details": data.get("api_details", {}),

    }
    print("Initial state sent to LangGraph:")
    print(json.dumps(state_update, indent=2))

    config = {"configurable": {"thread_id": "abc123"}}
    
    last_chunk = None

    # Start the test generation process
    try:
        print(f"Starting test generation using {approach} approach...")
        
        # Choose the appropriate graph based on the approach
        selected_graph = step_graph
        
        # Process the stream and push updates to the queue
        async for chunk in selected_graph.astream(state_update, config, stream_mode="custom"):
            # Add each chunk of data to the global queue
            await data_queue.put(chunk)
            print(f"Added to queue: {chunk}")
            
            last_chunk = chunk
            
        script = last_chunk['message'] if isinstance(last_chunk, dict) and 'message' in last_chunk else last_chunk
            
        return {"status": "Test generation successfully completed", "script": script}
    except Exception as e:
        print("Test generation failed:", str(e))
        raise HTTPException(status_code=500, detail=f"Test generation failed: {str(e)}")
    finally:
        job_cancellation_flags["current_job"] = False


# SSE endpoint to stream test results
@app.get("/stream_test_results")
async def stream_test_results():
    async def event_publisher():
        try:
            while True:
                # Wait for new data in the queue
                print("Waiting for data...")
                chunk = await data_queue.get()
                print(f"Sending chunk: {chunk}")
                # Send data as SSE
                yield f"{json.dumps(chunk)}\n\n"
        except Exception as e:
            yield f"{json.dumps({'error': str(e)})}\n\n"

    return EventSourceResponse(event_publisher())

# Add documentation for the API
@app.get("/")
async def root():
    return {
        "name": "ArchiTest API",
        "description": "API for generating test scripts using ArchiTest",
        "version": "1.0.0",
        "endpoints": [
            {
                "path": "/generate_tests",
                "method": "POST",
                "description": "Generate test scripts",
                "required_fields": ["url", "test_steps", "html_content", "framework"],
                "optional_fields": [
                    "approach", # 'legacy' (default) or 'step_by_step'
                    "language", # 'python' (default) or 'java' or 'javascript'
                    "max_retries" # default: 10
                ]
            },
            {
                "path": "/stream_test_results",
                "method": "GET",
                "description": "Stream test generation results using Server-Sent Events (SSE)"
            }
        ]
    }

@app.post("/cancel_generation")
async def cancel_generation():
    """Cancel ongoing test generation"""
    job_cancellation_flags["current_job"] = True
    await data_queue.put({"type": "info", "message": "Test generation cancelled"})
    return {"status": "cancelled"}