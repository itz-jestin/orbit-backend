import os
from langchain_openai import ChatOpenAI
from langchain_core.rate_limiters import InMemoryRateLimiter

# Works with OpenAI by default. To use another OpenAI-compatible provider,
# set LLM_BASE_URL, LLM_MODEL and LLM_API_KEY in the environment.
LLM_API_KEY = (os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY") or "").strip()
if not LLM_API_KEY:
    raise RuntimeError("Set OPENAI_API_KEY (or LLM_API_KEY) in the environment")

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "").strip() or None  # None = OpenAI
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini").strip()
LLM_RPM = float(os.getenv("LLM_RPM", "0"))  # 0 = no rate limit

print(f"LLM config -> model={LLM_MODEL!r}, base_url={LLM_BASE_URL or 'OpenAI default'!r}", flush=True)

rate_limiter = None
if LLM_RPM > 0:
    rate_limiter = InMemoryRateLimiter(
        requests_per_second=LLM_RPM / 60,
        check_every_n_seconds=0.5,
        max_bucket_size=1,
    )

llm = ChatOpenAI(
    model=LLM_MODEL,
    api_key=LLM_API_KEY,
    base_url=LLM_BASE_URL,
    temperature=0,
    timeout=60,
    max_retries=2,
    rate_limiter=rate_limiter,
)
