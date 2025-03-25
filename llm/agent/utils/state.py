from typing import Annotated, Optional
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
    language: Optional[str]  # Add this line
