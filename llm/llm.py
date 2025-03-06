import os 
from dotenv import load_dotenv 
from langchain_openai import AzureChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from typing import Annotated, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import requests

# Load environment variables from .env file 
load_dotenv() 

class CustomState(TypedDict):
    messages: Annotated[list, add_messages]
    url: str
    test_steps: str
    html_content: Optional[str]

# Initialize Azure OpenAI LLM 
llm = AzureChatOpenAI( 
    deployment_name=os.getenv("OPENAI_API_DEPLOYMENT"),
    model=os.getenv("OPENAI_API_MODEL"),
    temperature=0.8,
    max_tokens=1000
)

# Define a new graph
workflow = StateGraph(CustomState)

# Action taken by the home node
def invoke_llm(state: CustomState):
    prompt_template = ChatPromptTemplate([
        ("system", """
         You are a test script generator. Generate only a Python Playwright test script for the given HTML content and test steps. 
         Do not include any explanations, comments, or additional text.

        Test Steps:
        {test_steps}

        HTML Content:
        {html_content}
        """
        ),
        MessagesPlaceholder("messages")
    ])
    prompt = prompt_template.invoke(state)
    response = llm.invoke(prompt)
    return {"messages": response}

def extract_html(state: CustomState) -> CustomState:
    """Extract HTML from the provided URL"""
    url = state["url"]
    print(f"Extracting HTML from {url}")
    
    try:
        # Basic HTML extraction using requests
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        html_content = response.text
        
        # In a production system, you would use a headless browser like Playwright here
        # to handle JavaScript rendering, authentication, etc.
        
        state["html_content"] = html_content
        state["messages"].append({"role": "system", "content": f"Successfully extracted HTML from {url}."})
    except Exception as e:
        state["messages"].append({"role": "system", "content": f"Failed to extract HTML: {str(e)}"})
    
    # print(f"Extracted HTML: {html_content}")
    return state
# Define a graph with a single node
workflow.add_node("home", invoke_llm)
workflow.add_node("extract_html", extract_html)
workflow.add_edge(START, "extract_html")
workflow.add_edge("extract_html", "home")

# Compile the workflow, specifying a checkpointer
# that persists checkpoints to memory
memory = MemorySaver()
graph = workflow.compile(checkpointer=memory)
