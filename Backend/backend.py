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
from get_html import clean_html, extract_automation_elements, get_html, count_tokens, optimize_html_for_llm
from clean_html import clean_html_for_tests
from html_processor import HTMLProcessor
from sse_starlette.sse import EventSourceResponse
import json
import aiohttp
import requests
import asyncio
import time
from datetime import datetime

app = FastAPI()
html_processor = HTMLProcessor()


# Define the request body model using Pydantic
class TestRequest(BaseModel):
    url: List[str]
    test_steps: str
    framework: str
    language: str
    max_retries: int


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
    start_time = time.time()
    print(f"\nStarting URL processing at {datetime.now().strftime('%H:%M:%S')}")

    async def process_url(url):
        url_start_time = time.time()
        html_content = await get_html(url)  # Fetch HTML
        cleaned_html = clean_html(html_content)  # Clean HTML
        processed_html = extract_automation_elements(cleaned_html)  # Process HTML
        optimized_html = optimize_html_for_llm(processed_html)
        
        combined_html_text = str(optimized_html)
        token_count = count_tokens(combined_html_text, model="gpt-4")
        url_end_time = time.time()
        url_duration = url_end_time - url_start_time
        print(f"{url} => {token_count} tokens (processed in {url_duration:.2f} seconds)")
        return {
            "url": url,
            "html_elements": optimized_html,
            "token_count": token_count,
            "processing_time": url_duration
        }

    # Process all URLs concurrently using asyncio.gather
    results = await asyncio.gather(*[process_url(url) for url in request.url])
    
    # Calculate total tokens and processing times
    total_tokens = sum(result["token_count"] for result in results)
    total_time = time.time() - start_time
    avg_time_per_url = total_time / len(request.url)
    
    print(f"\nProcessing Summary:")
    print(f"Total URLs processed: {len(request.url)}")
    print(f"Total tokens: {total_tokens}")
    print(f"Total processing time: {total_time:.2f} seconds")
    print(f"Average time per URL: {avg_time_per_url:.2f} seconds")
    print(f"Concurrent processing speedup: {len(request.url) * avg_time_per_url / total_time:.2f}x")
    print("Max retries received from frontend:", request.max_retries)

    # Prepare the payload to send to the llm server
    payload = {
        "url": request.url[0],
        "test_steps": request.test_steps,
        "html_content": [{"url": result["url"], "html": result["html_elements"]} for result in results],
        "max_retries": request.max_retries,
        "framework": request.framework,
        "language": request.language,
    }

    print("Payload sent to LLM server:")
    print(json.dumps(payload, indent=2))

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
