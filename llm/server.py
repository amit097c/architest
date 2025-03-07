from fastapi import FastAPI, Request
from pydantic import BaseModel
from agent.agent import graph
from langchain_core.messages import HumanMessage

app = FastAPI()


# Define the request body model using Pydantic
class PromptReq(BaseModel):
    prompt: str


@app.get("/")
async def get():
    return {"message": "Hello, World!"}


@app.post("/")
async def chat(request: Request):
    data = await request.json()

    # Initialize state with required fields
    state_update = {
        "messages": [],
        "url": data.get("url", ""),
        "test_steps": data.get("test_steps", ""),
        "html_content": None,
        "has_errors": False,
        "error_message": None,
    }

    config = {"configurable": {"thread_id": "abc123"}}
    output = graph.invoke(state_update, config)
    return {"message": output["messages"][-1].content}
