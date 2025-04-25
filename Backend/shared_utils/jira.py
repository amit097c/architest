import aiohttp
import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth
import re
from fastapi import Request

load_dotenv()
jira_router = APIRouter()

class JiraRequest(BaseModel):
    issue_key: str
    email: str
    api_token: str
    domain: str

def build_jira_base(domain: str) -> str:
    return f"{domain}/rest/api/3"

@jira_router.post("/fetch_jira_test_steps")
def fetch_jira_test_steps(data: JiraRequest):
    try:
        auth = HTTPBasicAuth(data.email, data.api_token)
        jira_api_base = f"{data.domain}/rest/api/3"
        steps, url = get_test_criteria_from_jira(data.issue_key, auth, jira_api_base)
        return {"test_steps": steps, "url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_test_criteria_from_jira(ticket_id, auth, jira_api_base):
    url = f"{jira_api_base}/issue/{ticket_id}"
    headers = {
        "Accept": "application/json"
    }

    response = requests.get(url, headers=headers, auth=auth)
    # print("STATUS:", response.status_code)
    # print("RESPONSE TEXT:", response.text)
    response.raise_for_status()
    data = response.json()

    description = data["fields"]["description"]["content"]
    flat_description = extract_plain_text(description)

    test_steps = extract_block(flat_description, "Test Steps")
    target_url = extract_block(flat_description, "Target URL")

    if not test_steps:
        print("[Fallback] Test steps section not found — using all plain text.")
        test_steps = flat_description

    if not target_url:
        print("[Fallback] Target URL section not found — using default or empty string.")
        target_url = ""

    return test_steps.strip(), target_url.strip()

def extract_block(text, header):
    pattern = rf"###{header}\n(.*?)(\n###|\Z)"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else ""

def extract_plain_text(description_json):
    lines = []
    for block in description_json:
        for inner in block.get("content", []):
            if inner.get("type") == "text":
                lines.append(inner["text"])
            elif inner.get("type") == "paragraph":
                lines.append("\n")
    return "\n".join(lines)

def add_comment_to_jira(ticket_id: str, message: str, email: str, token: str, domain: str):
    url = f"{build_jira_base(domain)}/issue/{ticket_id}/comment"
    payload = {
        "body": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": message
                        }
                    ]
                }
            ]
        }
    }

    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    auth = HTTPBasicAuth(email, token)
    response = requests.post(url, json=payload, headers=headers, auth=auth)
    response.raise_for_status()
    print(f"Comment added to {ticket_id}")

def move_ticket_to_next_status(ticket_id: str, email: str, token: str, domain: str, target_status_name: str = "Done"):
    transitions_url = f"{build_jira_base(domain)}/issue/{ticket_id}/transitions"
    headers = {"Accept": "application/json", "Content-Type": "application/json"}

    # Fetch all available transitions
    auth = HTTPBasicAuth(email, token)
    response = requests.get(transitions_url, headers=headers, auth=auth)
    response.raise_for_status()
    transitions = response.json().get("transitions", [])

    if not transitions:
        print("No transitions available for this ticket.")
        return

    # Find the transition with the desired status name
    transition = next((t for t in transitions if t["to"]["name"].lower() == target_status_name.lower()), None)

    if not transition:
        print(f"No transition found for target status: {target_status_name}")
        print("Available transitions:")
        for t in transitions:
            print(f"- {t['to']['name']}")
        return

    # Move to the target status
    payload = {"transition": {"id": transition["id"]}}
    move_response = requests.post(transitions_url, json=payload, headers=headers, auth=auth)
    move_response.raise_for_status()
    print(f"Ticket {ticket_id} moved to '{target_status_name}'")

def create_bug_ticket_for_failed_test(original_ticket_id: str, failure_message: str, email: str, token: str, domain: str):
    create_url = f"{build_jira_base(domain)}/issue"
    headers = {"Accept": "application/json", "Content-Type": "application/json"}

    payload = {
        "fields": {
            "project": {
                "key": original_ticket_id.split("-")[0]  # Extract project key from SCRUM-1
            },
            "summary": f"Test failed for {original_ticket_id}",
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": f"The test associated with {original_ticket_id} failed.\n\nFailure details:\n{failure_message}"
                            }
                        ]
                    }
                ]
            },
            "issuetype": {
                "name": "Bug"
            }
        }
    }
    auth = HTTPBasicAuth(email, token)
    response = requests.post(create_url, json=payload, headers=headers, auth=auth)
    response.raise_for_status()
    new_ticket = response.json()["key"]
    print(f"Created new bug ticket: {new_ticket}")

    # Optionally link the bug to the original ticket
    link_url = f"{build_jira_base(domain)}/issueLink"
    link_payload = {
        "type": {
            "name": "Relates"
        },
        "inwardIssue": {
            "key": new_ticket
        },
        "outwardIssue": {
            "key": original_ticket_id
        }
    }
    link_response = requests.post(link_url, json=link_payload, headers=headers, auth=auth)
    link_response.raise_for_status()
    print(f"Linked {new_ticket} to {original_ticket_id}") 