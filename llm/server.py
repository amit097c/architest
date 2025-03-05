from fastapi import FastAPI
from pydantic import BaseModel
from llm import graph
from langchain_core.messages import HumanMessage

app = FastAPI()

# Define the request body model using Pydantic
class PromptReq(BaseModel):
    prompt: str

@app.get("/")
async def get():
    return {"message": "Hello, World!"}

@app.post("/")
async def chat(request: PromptReq):
    config = {"configurable": {"thread_id": "abc123"}}
    messages = {"messages": [HumanMessage(request.prompt)]}
    state_update = {
        "messages": messages["messages"],
        "test_steps": """
            Navigate to a Page: It goes to the page for bags on the Magento Software Testing Board website.
            Interact with the Page:
            It clicks on a category in the menu (likely for a specific type of bag).
            It scrolls down to the bottom of the page to load more content.
            It clicks on a promotional text about a deal ("4 tees for the price of 3").
            Verify URL: It checks if the URL contains the word "tees" after clicking the promotion, ensuring the page has changed correctly.
        """,
        "url": "https://magento.softwaretestingboard.com"
    }
    output = graph.invoke(state_update, config)
    return {"message": output["messages"][-1].content}