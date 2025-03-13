import re
import os


def clean_script_response(response: str) -> str:
    """Remove Markdown code block syntax from the script response"""
    # Remove ```python at the start and ``` at the end
    cleaned = re.sub(r"^```python\n", "", response)
    cleaned = re.sub(r"\n```$", "", cleaned)
    # Also handle case where it's just ``` without python
    cleaned = re.sub(r"^```\n", "", cleaned)
    return cleaned.strip()


def retrieve_examples(query: str, examples_dir: str = "examples") -> list:
    examples = []
    print(f"examples_dir: {examples_dir}")
    for filename in os.listdir(examples_dir):
        if filename.endswith(".py"):
            with open(os.path.join(examples_dir, filename), "r") as file:
                content = file.read()
                if query.lower() in content.lower():
                    examples.append(content)
    print(examples)
    return examples