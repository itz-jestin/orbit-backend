import os
from langchain_openai import ChatOpenAI
from langchain_core.rate_limiters import InMemoryRateLimiter

BYNARA_API_KEY = os.getenv("BYNARA_API_KEY", "").strip()
if not BYNARA_API_KEY:
    raise RuntimeError("BYNARA_API_KEY is not set in the environment")

# Space out requests to stay within the provider's free-tier rate limit.
# Adjust LLM_RPM on Render once you know Bynara's actual limit.
LLM_RPM = float(os.getenv("LLM_RPM", "4.5"))

rate_limiter = InMemoryRateLimiter(
    requests_per_second=LLM_RPM / 60,
    check_every_n_seconds=0.5,
    max_bucket_size=1,
)

llm = ChatOpenAI(
    model=os.getenv("LLM_MODEL", "nemotron-3.5-lightning-free"),
    api_key=BYNARA_API_KEY,
    base_url="https://router.bynara.id/v1",
    temperature=0,
    timeout=60,
    max_retries=2,
    rate_limiter=rate_limiter,
)