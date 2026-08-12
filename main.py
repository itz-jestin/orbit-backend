from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from graph import graph
from pydantic import BaseModel
from utils.pdf_generator import generate_pdf
import os
from fastapi.responses import StreamingResponse
import json

from database import Base, engine
from auth_routes import router as auth_router
import auth_models  # noqa: F401 - ensures auth tables register with Base
import models        # noqa: F401 - ensures other tables (e.g. research history) register with Base

app = FastAPI(
    title="Research Assistant API",
    version="1.0.0",
    description="Multi-Agent Research Assistant using LangGraph"
)

# CORS
# NOTE: replace with your actual Vercel frontend URL once deployed.
# allow_origins=["*"] cannot be combined with allow_credentials=True per browser spec.
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

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

        async for event in graph.astream(state):
            print(event)

            yield f"data: {json.dumps(event, default=str)}\n\n"

            for _, value in event.items():
                if isinstance(value, dict):
                    final_state = value

        if final_state:
            yield f"data: {json.dumps({'done': True})}\n\n"

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

    path = f"reports/{filename}"

    if not os.path.exists(path):
        return {"error": "File not found"}

    return FileResponse(
        path=path,
        media_type="application/pdf",
        filename=filename
    )