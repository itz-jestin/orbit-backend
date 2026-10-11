import os
from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain_core.rate_limiters import InMemoryRateLimiter

BYNARA_API_KEY = os.getenv("BYNARA_API_KEY", "").strip()
if not BYNARA_API_KEY:
    raise RuntimeError("BYNARA_API_KEY is not set in the environment")

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://router.bynara.id/v1").strip()
LLM_MODEL = os.getenv("LLM_MODEL", "nemotron-3.5-lightning-free").strip()
LLM_RPM = float(os.getenv("LLM_RPM", "4.5"))

print(f"LLM config -> model={LLM_MODEL!r}, base_url={LLM_BASE_URL!r}", flush=True)

# Startup diagnostic: list the model IDs this provider actually accepts
try:
    available = [m.id for m in OpenAI(api_key=BYNARA_API_KEY, base_url=LLM_BASE_URL).models.list()]
    print(f"Provider models ({len(available)}): {available}", flush=True)
    if LLM_MODEL not in available:
        print(f"WARNING: {LLM_MODEL!r} is not in the provider's model list", flush=True)
except Exception as e:
    print(f"Could not list provider models: {e}", flush=True)

rate_limiter = InMemoryRateLimiter(
    requests_per_second=LLM_RPM / 60,
    check_every_n_seconds=0.5,
    max_bucket_size=1,
)

llm = ChatOpenAI(
    model=LLM_MODEL,
    api_key=BYNARA_API_KEY,
    base_url=LLM_BASE_URL,
    temperature=0,
    timeout=60,
    max_retries=2,
    rate_limiter=rate_limiter,
)