from typing import Annotated, Optional, Dict
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages



class CustomState(TypedDict):
    messages: Annotated[list, add_messages]
    url: str
    test_steps: str
    html_content: Optional[str]
    has_errors: Optional[bool]
    error_message: Optional[str]
    execution_time: Optional[float]
    success_rate: Optional[float]
    error_rate: Optional[float]
    retry_count: Optional[int]
    framework: Optional[str]
    language: Optional[str]
    last_script: Optional[str] = None
    max_retries: Optional[int] = None
    # Fields for step-by-step execution
    current_step_index: Optional[int] = 0
    current_step: Optional[str] = None
    steps_list: Optional[list] = None
    completed_steps: Optional[list] = []
    accumulated_script: Optional[str] = None
    generated_selectors: Optional[dict] = {}
    api_results: Optional[dict] = {}  # Kept for future compatibility
    jira_ticket_id: Optional[str] = None
    jira_email: Optional[str] = None
    jira_token: Optional[str] = None
    jira_domain: Optional[str] = None
    is_api_test: Optional[bool] = False
    api_details: Optional[Dict[str, str]] = None
