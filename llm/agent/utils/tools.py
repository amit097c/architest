import re


def clean_script_response(response: str) -> str:
    """Remove Markdown code block syntax from the script response"""
    # Remove ```python at the start and ``` at the end
    cleaned = re.sub(r"^```(python|java)\n", "", response)
    cleaned = re.sub(r"\n```$", "", cleaned)
    # Also handle case where it's just ``` without python
    cleaned = re.sub(r"^```\n", "", cleaned)
    return cleaned.strip()