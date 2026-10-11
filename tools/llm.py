import os
from langchain_openai import ChatOpenAI
from langchain_core.rate_limiters import InMemoryRateLimiter

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not set in the environment")

# Free tier allows 5 requests/minute for this model: allow 1 request every ~13 seconds
rate_limiter = InMemoryRateLimiter(
    requests_per_second=4.5 / 60,
    check_every_n_seconds=0.5,
    max_bucket_size=1,
)

llm = ChatOpenAI(
    model=os.getenv("LLM_MODEL", "ling-3.0-flash-fin-free"),
    api_key=BYNARA_API_KEY,
    base_url="https://router.bynara.id/v1",
    temperature=0,
    timeout=60,
    max_retries=2,
    rate_limiter=rate_limiter,
)