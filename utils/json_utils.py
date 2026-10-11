import json
import re


def extract_json(content):
    """Pull a JSON object/array out of a model reply that may contain
    <think> blocks, ```json fences, or extra text around the JSON."""
    if isinstance(content, list):  # some providers return content blocks
        content = "".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in content
        )
    if not content or not str(content).strip():
        raise ValueError("empty model response")

    text = re.sub(r"<think>.*?</think>", "", str(content), flags=re.DOTALL).strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise