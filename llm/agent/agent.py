import os
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, StateGraph, END
from agent.utils.state import CustomState
from agent.utils.nodes import (
    clear_memory,
    handle_framework,
    limit_error,
    initialize_step_execution,
    process_current_step,
    retry_step,
    execute_step_script,
    execute_selenium_script,
    execute_playwright_js_script,
    execute_postman_collection,
    HAS_CACHE
)

from agent.prompts import (
    prompt_template_step,
    error_prompt_step,
    prompt_template_selenium,
    error_prompt_selenium,
    prompt_template_playwright_js,
    error_prompt_playwright_js,
    prompt_template_postman,
    error_prompt_postman
)
from agent.utils.tools import clean_script_response

# Conditionally import LLMCache if available
if HAS_CACHE:
    from agent.utils.nodes import LLMCache

# Check if running in GitHub Actions
if os.getenv("ENV") != "production":
    # Load environment variables from .env file (for local testing)
    if not load_dotenv():
        raise RuntimeError("Failed to load environment variables from .env file")
    
# Initialize Azure OpenAI LLM
try:
    # Try to initialize with cache if available
    cache_instance = None
    if HAS_CACHE:
        try:
            cache_instance = LLMCache()
        except Exception as cache_error:
            print(f"Cache initialization failed, continuing without cache: {cache_error}")
    
    llm = AzureChatOpenAI(
        deployment_name=os.getenv("OPENAI_API_DEPLOYMENT"),
        model=os.getenv("OPENAI_API_MODEL"),
        temperature=0.2,
        max_tokens=3000,
        cache=cache_instance,
    )
except Exception as e:
    raise RuntimeError(f"Failed to initialize Azure OpenAI LLM: {str(e)}")

# Define a new graph
workflow = StateGraph(CustomState)

# Add memory saver instance after the workflow definition
memory_saver = MemorySaver()

# Define the step-by-step workflow
step_workflow = StateGraph(CustomState)

# Define nodes for step-by-step workflow
step_workflow.add_node("initialize", lambda state, writer: initialize_step_execution(state, writer))
step_workflow.add_node("process_step", lambda state, writer: process_current_step(state, llm, prompt_template_step, prompt_template_selenium, prompt_template_playwright_js, prompt_template_postman, writer))
step_workflow.add_node("execute_step", lambda state, writer: execute_step_script(state, writer))
step_workflow.add_node("execute_playwright_js", lambda state, writer: execute_playwright_js_script(state, writer))
step_workflow.add_node("execute_selenium", lambda state, writer: execute_selenium_script(state, writer))
step_workflow.add_node("execute_postman", lambda state, writer: execute_postman_collection(state, writer))
step_workflow.add_node("retry_step", lambda state, writer: retry_step(state, llm, error_prompt_step, error_prompt_playwright_js, error_prompt_selenium, error_prompt_postman, writer))
# step_workflow.add_node("check_stop", lambda state, writer: check_stop(state, writer))
step_workflow.add_node("clear", clear_memory)

# Define the flow for step-by-step workflow
step_workflow.add_edge(START, "initialize")
step_workflow.add_edge("initialize", "process_step")
# step_workflow.add_edge("process_step", "execute_step")
step_workflow.add_conditional_edges("process_step", handle_framework, {
    "execute_playwright_script": "execute_step",
    "execute_selenium_script": "execute_selenium",
    "execute_playwright_js_script": "execute_playwright_js",
    "execute_postman_collection": "execute_postman"
})

step_workflow.add_conditional_edges(
    "retry_step", limit_error, {
        "execute_selenium": "execute_selenium",
        "execute_playwright": "execute_step",
        "execute_playwright_js": "execute_playwright_js",
        "execute_postman": "execute_postman",
        "stop": "clear"
    }
)
step_workflow.add_edge("clear", END)

# Add conditional edges based on execution results
class StepRouter:
    def __call__(self, state):
        # Check if we need to stop execution
        if state.get("stop_execution", False):
            return "stop"

        # If there are errors, retry
        if state.get("has_errors", False):
            return "retry"
        
        # Check if we've completed all steps
        next_step_index = state["current_step_index"]
        
        # If we're at the last step and it was executed successfully, return "complete"
        if next_step_index >= len(state["steps_list"]) and state["has_errors"] == False:
            return "complete"
            
        # If we have more steps, continue to the next one
        if next_step_index < len(state["steps_list"]):
            state["current_step_index"] = next_step_index
            state["current_step"] = state["steps_list"][next_step_index]
            return "continue"
        
        # Otherwise, stay on the current step (should not happen normally)
        return "continue"

step_workflow.add_conditional_edges(
    "execute_step", 
    StepRouter(),
    {
        "retry": "retry_step",
        "continue": "process_step",
        "complete": "clear",
        "stop": "clear"
    }
)

step_workflow.add_conditional_edges(
    "execute_selenium", 
    StepRouter(),
    {
        "retry": "retry_step",
        "continue": "process_step",
        "complete": "clear",
        "stop": "clear"
    }
)
step_workflow.add_conditional_edges(
    "execute_playwright_js", 
    StepRouter(),
    {
        "retry": "retry_step",
        "continue": "process_step",
        "complete": "clear",
        "stop": "clear"
    }
)
step_workflow.add_conditional_edges(
    "execute_postman", 
    StepRouter(),
    {
        "retry": "retry_step",
        "continue": "process_step",
        "complete": "clear",
        "stop": "clear"
    }
)

# Compile the workflows
try:
    config = {"memory": memory_saver}
    step_graph = step_workflow.compile()
except Exception as e:
    raise RuntimeError(f"Failed to compile workflow: {str(e)}")

# Export both graphs
__all__ = ["step_graph"]
