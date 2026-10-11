from langchain_openai import ChatOpenAI

from config import OPENAI_API_KEY


llm = ChatOpenAI(
    model="deepseek-ai/deepseek-v4.1-flash",
    api_key=OPENAI_API_KEY,
    base_url="https://integrate.api.nvidia.com/v1",
    temperature=0,
    timeout=120,        # seconds — fail fast instead of hanging forever
    max_retries=2,      # let the client retry transient failures automatically
)