import os
from langchain_openai import ChatOpenAI

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not set in the environment")

llm = ChatOpenAI(
    model=os.getenv("LLM_MODEL", "gemini-3.8-flash"),
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    temperature=0,
    timeout=60,
    max_retries=2,
)