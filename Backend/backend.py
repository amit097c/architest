import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import os
from get_html import get_html
from clean_html import clean_html_for_tests
from html_processor import HTMLProcessor

app = FastAPI()
html_processor = HTMLProcessor(log_level=logging.DEBUG)

# Define the request body model using Pydantic
class TestRequest(BaseModel):
    url: str
    test_steps: str

@app.post("/send_test")
async def send_test(request: TestRequest):
    # Extract
    html_content = get_html(request.url)
    
    cleaned_html = clean_html_for_tests(html_content)
    
    processed_html = html_processor.process_html(cleaned_html)

    #if not processed_html:
    #    raise HTTPException(status_code=500, detail="Failed to extract and process HTML from the provided URL.")

    # Prepare the payload to send to the llm server
    payload = {
        "url": request.url,
        "test_steps": request.test_steps,
        "html_content": processed_html
    }

    # Send the payload to the llm server
    llm_server_url = "http://localhost:8000/"  # Adjust the URL if needed
    try:
        response = requests.post(llm_server_url, json=payload)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error sending request to LLM server: {e}")
        raise HTTPException(status_code=500, detail=f"Error sending request to LLM server: {e}")

    print("Response from LLM server:", response.json())
    return response.json()