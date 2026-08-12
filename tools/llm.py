from langchain_openai import ChatOpenAI

from config import OPENAI_API_KEY


llm = ChatOpenAI(
    model="meta/llama-3.1-8b-instruct",
    api_key=OPENAI_API_KEY,
    base_url="https://integrate.api.nvidia.com/v1",
    temperature=0,
    timeout=30,        # seconds — fail fast instead of hanging forever
    max_retries=2,      # let the client retry transient failures automatically
)