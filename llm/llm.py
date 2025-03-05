import os 
from dotenv import load_dotenv 
from langchain_openai import AzureChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# Load environment variables from .env file 
load_dotenv() 

class CustomState(TypedDict):
    messages: Annotated[list, add_messages]
    url: str
    test_steps: str

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
         You are ArchiTest, an AI-powered tool for generating python Playwright test scripts. The goal is to create an automated test script from a given URL and a series of test steps. 

        Please follow these instructions:
        1. Extract the essential HTML elements from the webpage at the provided URL.
        2. Process the HTML to retain the necessary elements relevant to the test steps.
        3. For each of the provided test steps, generate a python Playwright test script that interacts with the page according to those steps.

        Test Steps:
        {test_steps}

        URL:
        {url}

        Output:
        Generate a python Playwright test script that performs the following actions, ensuring to check for any necessary conditions like loading, wait times, and proper API responses. If a step involves interacting with an element, ensure to specify the correct locator strategy (e.g., CSS selector, XPath). Make sure the script is fully executable and efficient for the test scenario.

        Once the script is generated, simulate its execution and ensure it passes all tests. If the script fails any step, refine the generated script to resolve the issues and provide the corrected version.

        Make sure to:
        - Optimize for speed and reliability.
        - Ensure compatibility with common frameworks like Cypress and Selenium where applicable.
        - Output the final test script in a clear, formatted way that can be directly used in a CI/CD pipeline.

        Refined Test Script:
        """
        ),
        MessagesPlaceholder("messages")
    ])
    prompt = prompt_template.invoke(state)
    response = llm.invoke(prompt)
    return {"messages": response}

# Define a graph with a single node
workflow.add_edge(START, "home")
workflow.add_node("home", invoke_llm)

# Compile the workflow, specifying a checkpointer
# that persists checkpoints to memory
memory = MemorySaver()
graph = workflow.compile(checkpointer=memory)
