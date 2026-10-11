from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import json
import asyncio
import traceback

from graph import graph
from utils.pdf_generator import generate_pdf  # noqa: F401 - kept for PDF report generation

from database import Base, engine, SessionLocal
from auth_routes import router as auth_router
import auth_models  # noqa: F401 - ensures auth tables register with Base
import models        # noqa: F401 - ensures other tables (e.g. research history) register with Base

app = FastAPI(
    title="Research Assistant API",
    version="1.0.0",
    description="Multi-Agent Research Assistant using LangGraph"
)

# CORS
# Strips spaces and trailing slashes so small typos in the env var don't break matching
ALLOWED_ORIGINS = [
    origin.strip().rstrip("/")
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]
print("CORS allowed origins:", ALLOWED_ORIGINS, flush=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Creates orbit.db (or Postgres tables) on first run.
Base.metadata.create_all(bind=engine)
app.include_router(auth_router)

# How often to send a keep-alive while waiting for slow LLM calls.
# Proxies in front of Render can drop a stream that stays silent too long.
HEARTBEAT_SECONDS = 15


@app.get("/")
async def home():
    return {
        "message": "Research Assistant API is running"
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy"
    }


@app.get("/health/db")
async def health_db():
    from sqlalchemy import text
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "db": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "db": "error", "detail": str(e)}
    finally:
        db.close()


class QueryRequest(BaseModel):
    query: str


@app.post("/research")
async def research(request: QueryRequest):

    state = {
        "query": request.query,
        "sub_questions": [],
        "research_results": [],
        "final_report": "",
        "critique": {},
        "feedback": "",
        "retries": 0,
        "revised": False,
    }

    async def event_generator():
        queue: asyncio.Queue = asyncio.Queue()

        # Runs the LangGraph pipeline in the background and pushes results into the queue
        async def run_graph():
            try:
                async for event in graph.astream(state):
                    print(event, flush=True)
                    await queue.put(("event", event))
                await queue.put(("end", None))
            except Exception as e:
                print("RESEARCH PIPELINE FAILED:", flush=True)
                traceback.print_exc()
                await queue.put(("error", f"{type(e).__name__}: {e}"))

        task = asyncio.create_task(run_graph())
        final_state = None

        try:
            while True:
                try:
                    kind, payload = await asyncio.wait_for(queue.get(), timeout=HEARTBEAT_SECONDS)
                except asyncio.TimeoutError:
                    # SSE comment line: keeps the connection alive, ignored by event parsers
                    yield ": keepalive\n\n"
                    continue

                if kind == "event":
                    yield f"data: {json.dumps(payload, default=str)}\n\n"
                    for _, value in payload.items():
                        if isinstance(value, dict):
                            final_state = value

                elif kind == "error":
                    yield f"data: {json.dumps({'error': payload})}\n\n"
                    break

                else:  # "end"
                    if final_state:
                        yield f"data: {json.dumps({'done': True})}\n\n"
                    else:
                        print("RESEARCH PIPELINE ENDED WITHOUT ANY STATE", flush=True)
                        yield f"data: {json.dumps({'error': 'Pipeline finished without producing a result'})}\n\n"
                    break
        finally:
            # If the browser disconnects, stop the pipeline so it doesn't keep spending API calls
            if not task.done():
                print("Client disconnected; cancelling research pipeline", flush=True)
                task.cancel()

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/download/{filename}")
async def download_report(filename: str):

    # basename() blocks paths like "../../etc/passwd"
    safe_name = os.path.basename(filename)
    path = os.path.join("reports", safe_name)

    if not os.path.exists(path):
        return {"error": "File not found"}

    return FileResponse(
        path=path,
        media_type="application/pdf",
        filename=safe_name
    )