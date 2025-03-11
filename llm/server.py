from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from agent.agent import graph

app = FastAPI()


# Define the request body model using Pydantic
class PromptReq(BaseModel):
    prompt: str


@app.get("/")
async def get():
    return {"message": "Hello, World!"}


@app.post("/")
async def chat(request: Request):
    try:
        data = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")

    # Validate required fields
    required_fields = ["url", "test_steps", "html_content"]
    for field in required_fields:
        if field not in data:
            raise HTTPException(
                status_code=400, detail=f"Missing required field: {field}"
            )

    # Initialize state with required fields
    state_update = {
        "messages": [],
        "url": data.get("url", ""),
        "test_steps": data.get("test_steps", ""),
        "html_content": data.get("html_content", ""),
        "has_errors": False,
        "error_message": None,
    }

    config = {"configurable": {"thread_id": "abc123"}}

    try:
        output = graph.invoke(state_update, config)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Graph invocation failed: {str(e)}"
        )

    if not output["messages"]:
        raise HTTPException(status_code=500, detail="No messages in output")

    return {"message": output["messages"][-1].content}
