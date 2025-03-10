from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import os
from get_html import get_html
from clean_html import clean_html_for_tests
from html_processor import HTMLProcessor

app = FastAPI()

html_processor = HTMLProcessor()

# Define the request body model using Pydantic
class TestRequest(BaseModel):
    url: str
    test_steps: str

@app.post("/send_test")
async def send_test(request: TestRequest):

    print(f"Extracting HTML from: {request.url}")
    extracted_html = get_html(request.url)
    
    if not extracted_html:
        raise HTTPException(status_code=500, detail="Failed to extract HTML from the provided URL.")

    print("Cleaning extracted HTML...")
    cleaned_html = clean_html_for_tests(extracted_html)
    
    if not cleaned_html:
        raise HTTPException(status_code=500, detail="Failed to clean extracted HTML.")
    
    print("Processing cleaned HTML...")
    processed_data = html_processor.process_html()

    if not processed_data:
        raise HTTPException(status_code=500, detail="Failed to process cleaned HTML.")

    # Read HTML content from the extracted_files folder
    html_file_path = os.path.join("extracted_files", "processed_html_output.json")
    if not os.path.exists(html_file_path):
        raise HTTPException(status_code=404, detail="HTML file not found")

    with open(html_file_path, "r", encoding="utf-8") as file:
        html_content = file.read()

    # Prepare the payload to send to the llm server
    payload = {
        "url": request.url,
        "test_steps": request.test_steps,
        "html_content": html_content
    }

    # Send the payload to the llm server
    llm_server_url = "http://localhost:8000/"  # Adjust the URL if needed
    response = requests.post(llm_server_url, json=payload)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    return response.json()