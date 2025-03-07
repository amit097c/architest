import requests
import tempfile
import subprocess
import os
from agent.utils.tools import clean_script_response, retrieve_examples


def extract_html(state):
    url = state["url"]
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        html_content = response.text
        state["html_content"] = html_content
        state["messages"].append(
            {"role": "system", "content": f"Successfully extracted HTML from {url}."}
        )
    except Exception as e:
        state["messages"].append(
            {"role": "system", "content": f"Failed to extract HTML: {str(e)}"}
        )
    return state


def invoke_llm(state, llm, prompt_template):
    query = f"Generate Playwright test for {state['test_steps']}"
    examples = retrieve_examples(query)

    prompt = prompt_template.invoke(
        {
            "test_steps": state["test_steps"],
            "html_content": state["html_content"],
            "examples": "\n\n".join(examples),
            "messages": state["messages"],
        }
    )
    response = llm.invoke(prompt)
    cleaned_content = clean_script_response(response.content)
    return {"messages": [{"role": "assistant", "content": cleaned_content}]}


def execute_playwright_script(state):
    script_content = state["messages"][-1].content
    print("\n=== Generated Script ===")
    print(script_content)
    print("=====================\n")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        if "async def" in script_content:
            wrapper_script = f"""
            import asyncio
            {script_content}

            test_func = [f for f in locals().values() if callable(f) and f.__name__.startswith('test_')][0]
            asyncio.run(test_func())
            """
            f.write(wrapper_script)
        else:
            f.write(script_content)
        temp_path = f.name

    try:
        subprocess.run(["pip", "install", "playwright"], check=True)
        subprocess.run(["playwright", "install"], check=True)

        process = subprocess.run(["python", temp_path], capture_output=True, text=True)
        if process.returncode != 0:
            print("\n=== Execution Error ===")
            print(process.stderr)
            print("=====================\n")
            state["messages"].append(
                {
                    "role": "system",
                    "content": f"Script execution failed with error: {process.stderr}",
                }
            )
            state["has_errors"] = True
            state["error_message"] = process.stderr
        else:
            print("\n=== Success ===")
            print("Script executed without errors")
            print("=============\n")
            state["messages"].append(
                {"role": "system", "content": "Script executed successfully"}
            )
            state["has_errors"] = False
    finally:
        os.unlink(temp_path)
    return state


def handle_errors(state):
    return "retry" if state.get("has_errors", False) else "success"


def retry_with_errors(state, llm, error_prompt):
    print("\n=== Retrying with error ===")
    print(f"Error message: {state['error_message']}")
    print("========================\n")

    prompt = error_prompt.invoke(
        {
            "original_script": state["messages"][-2].content,
            "error_message": state["error_message"],
            "url": state["url"],
            "test_steps": state["test_steps"],
        }
    )

    response = llm.invoke(prompt)
    cleaned_content = clean_script_response(response.content)

    return {
        **state,
        "messages": [{"role": "assistant", "content": cleaned_content}],
        "has_errors": False,
        "error_message": None,
    }
