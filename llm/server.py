from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
import json
import asyncio
from agent.agent import graph

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
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")

    # Validate required fields
    required_fields = ["url", "test_steps", "html_content","framework"]
    for field in required_fields:
        if field not in data:
            raise HTTPException(
                status_code=400, detail=f"Missing required field: {field}"
            )

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
    }
    print("Initial state sent to LangGraph:")
    print(json.dumps(state_update, indent=2))

    config = {"configurable": {"thread_id": "abc123"}}

    # Start the test generation process
    try:
        print("Starting test generation...")
        # Process the stream and push updates to the queue
        async for chunk in graph.astream(state_update, config, stream_mode="custom"):
            # Add each chunk of data to the global queue
            await data_queue.put(chunk)
            print(f"Added to queue: {chunk}")
        return {"status": "Test generation started successfully"}
    except Exception as e:
        print("Test generation failed:", str(e))
        raise HTTPException(status_code=500, detail=f"Test generation failed: {str(e)}")


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
