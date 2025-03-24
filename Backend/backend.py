"""
backend.py

This FastAPI backend handles:
- Extracting HTML from a given URL (`get_html.py`).
- Cleaning and processing the extracted HTML (`clean_html.py` and `html_processor.py`).
- Sending the processed data to an LLM-based test script generator.
- Streaming real-time test execution results using SSE.

Key Features:
- `/send_test`: Extracts, cleans, processes, and sends HTML to LLM for test generation.
- `/stream`: Streams live test execution results to the frontend.
- Uses `aiohttp` for asynchronous requests and `sse-starlette` for Server-Sent Events (SSE).

"""

import logging
from typing import List
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from get_html import get_html, count_tokens
from clean_html import clean_html_for_tests
from html_processor import HTMLProcessor
from sse_starlette.sse import EventSourceResponse
import json
import aiohttp
import requests

app = FastAPI()
html_processor = HTMLProcessor()


# Define the request body model using Pydantic
class TestRequest(BaseModel):
    url: List[str]
    test_steps: str
    framework: str


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Adjust this to your frontend's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/send_test")
async def send_test(request: TestRequest):
    # Extract HTML for each selected page
    page_contents = []
    total_tokens = 0

    for url in request.url:
        html_content = get_html(url)  # Fetch HTML
        cleaned_html = clean_html_for_tests(html_content)  # Clean HTML
        # processed_html = html_processor.process_html(cleaned_html)  # Process HTML
        
        combined_html_text = str(cleaned_html)
        token_count = count_tokens(combined_html_text, model="gpt-4")
        print(f"{url} => {token_count} tokens")
        total_tokens += token_count
        # Store structured data
        page_contents.append({"url": url, "html": cleaned_html})

    print(f"Total tokens: {total_tokens}")
    # Prepare the payload to send to the llm server
    payload = {
        "url": request.url[0],
        "test_steps": request.test_steps,
        "html_content": page_contents,
        "framework": request.framework,
    }

    # Send the payload to the llm server
    llm_server_url = "http://localhost:8000/generate_tests"  # Adjust the URL if needed

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(llm_server_url, json=payload) as response:
                response.raise_for_status()
                response_data = await response.json()  # Async handling of the response
                print("Response from LLM server:", response_data)
                return response_data
    except aiohttp.ClientError as e:
        print(f"Error sending request to LLM server: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error sending request to LLM server: {e}"
        )


@app.get("/stream")
async def stream():
    """
    This endpoint streams the results of a test from the LLM server via SSE.
    It fetches chunks of data from the LLM server and sends them to the frontend in real-time.
    """

    async def event_publisher():
        llm_sse_url = (
            "http://localhost:8000/stream_test_results"  # Adjust the URL if needed
        )

        print("Connecting to LLM SSE stream...")

        # Set up the HTTP connection to the LLM server's SSE endpoint
        async with aiohttp.ClientSession() as session:
            async with session.get(llm_sse_url) as response:
                if response.status != 200:
                    yield {"event": "error", "data": "Error from LLM server"}
                    return

                print("Successfully connected to /stream_test_results")

                # Read chunks of data from the LLM server's SSE stream
                async for line in response.content:
                    chunk = line.decode().strip()

                    # Skip empty lines
                    if not chunk:
                        continue

                    print(f"Received chunk: {chunk}")

                    # Process the chunk to extract the JSON payload
                    if chunk.startswith(
                        "data: "
                    ):  # Ensure the chunk starts with "data: "
                        json_data = chunk[6:].strip()  # Remove "data: " prefix
                    else:
                        json_data = chunk  # Fallback in case prefix is missing
                    # {"type": "info", "message": "Generating script"}
                    # Try parsing the JSON data
                    
                    try:
                        data = json.loads(json_data)  # Parse the chunk as JSON
                        print("DATA:")
                        print(data)
                        message = json.dumps(data)
                        yield {"event": "message", "data": message}  # Send it as SSE event
                    except json.JSONDecodeError as e:
                        print(f"JSON decode error: {e}, Raw chunk: {json_data}")

    # Return the EventSourceResponse to stream the results to the frontend
    return EventSourceResponse(event_publisher())
