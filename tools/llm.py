from langchain_openai import ChatOpenAI

from config import OPENAI_API_KEY


llm = ChatOpenAI(
    model="nvidia/nemotron-3.5-lightning-30b-a3b",
    api_key=OPENAI_API_KEY,
    base_url="https://integrate.api.nvidia.com/v1",
    temperature=0,
    timeout=120,        # seconds — fail fast instead of hanging forever
    max_retries=2,      # let the client retry transient failures automatically
)