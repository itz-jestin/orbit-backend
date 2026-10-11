import os
from langchain_openai import ChatOpenAI


llm = ChatOpenAI(
    model=os.getenv("LLM_MODEL", "gemini-2.5-flash"),
    api_key=os.getenv("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    temperature=0,
    timeout=60,        # Gemini Flash usually answers in seconds
    max_retries=2,     # retry brief hiccups like rate limits
)