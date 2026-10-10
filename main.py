from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import json
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
        final_state = None
        try:
            async for event in graph.astream(state):
                print(event, flush=True)

                yield f"data: {json.dumps(event, default=str)}\n\n"

                for _, value in event.items():
                    if isinstance(value, dict):
                        final_state = value

            if final_state:
                yield f"data: {json.dumps({'done': True})}\n\n"
            else:
                print("RESEARCH PIPELINE ENDED WITHOUT ANY STATE", flush=True)
                yield f"data: {json.dumps({'error': 'Pipeline finished without producing a result'})}\n\n"

        except Exception as e:
            # Log the full traceback to Render logs and tell the frontend what went wrong
            print("RESEARCH PIPELINE FAILED:", flush=True)
            traceback.print_exc()
            yield f"data: {json.dumps({'error': f'{type(e).__name__}: {e}'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
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
