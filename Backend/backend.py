from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import os

app = FastAPI()

# Define the request body model using Pydantic
class TestRequest(BaseModel):
    url: str
    test_steps: str

@app.post("/send_test")
async def send_test(request: TestRequest):
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