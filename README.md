# Orbit — Research Assistant API (Backend)

A multi-agent research assistant backend built with FastAPI and LangGraph. Runs a planner → researcher → writer → grounding_check → critic pipeline to answer research queries, with user auth and research history.

**Live API**: https://orbit-backend-lu7c.onrender.com
**Live App (frontend)**: https://6a7d446e627d58ddd0651cf6--orbitresearchagent.netlify.app/

## Tech Stack

- **Framework**: FastAPI
- **Agent orchestration**: LangGraph + LangChain
- **LLM**: OpenAI (via `langchain-openai`)
- **Search**: Tavily
- **Database**: SQLAlchemy ORM — SQLite locally, PostgreSQL in production (Neon)
- **Auth**: JWT (`python-jose`) + password hashing (`passlib[bcrypt]`)
- **PDF reports**: ReportLab
- **Tracing**: LangSmith
- **Deployment**: Docker on Render

## Project Structure

```
backend/
├── agents/          # Individual agent logic (planner, researcher, writer, critic, etc.)
├── prompts/         # Prompt templates for each agent
├── reports/          # Generated PDF research reports
├── schemas/         # Pydantic request/response schemas
├── tools/            # External tool integrations (search, etc.)
├── utils/            # Helper utilities (PDF generation, etc.)
├── auth.py            # Auth logic (JWT, password hashing)
├── auth_models.py     # SQLAlchemy models for users
├── auth_routes.py     # Auth API endpoints
├── auth_schemas.py    # Pydantic schemas for auth
├── config.py           # App configuration
├── database.py         # DB engine/session setup
├── graph.py             # LangGraph pipeline definition
├── main.py               # FastAPI app entrypoint
├── models.py              # SQLAlchemy models (research history, etc.)
├── state.py                # LangGraph state definitions
├── Dockerfile
└── requirements.txt
```

## Local Setup

1. Clone the repo and navigate to `backend/`
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Create a `.env` file with:
   ```
   OPENAI_API_KEY=your_key
   TAVILY_API_KEY=your_key
   LANGSMITH_API_KEY=your_key
   LANGSMITH_PROJECT=your_project
   LANGSMITH_TRACING=true
   DATABASE_URL=              # leave unset to use local SQLite
   ALLOWED_ORIGINS=http://localhost:5173,http://localhost:8080
   ```
4. Run the server:
   ```bash
   uvicorn main:app --reload
   ```
5. Visit `http://localhost:8000/docs` for the interactive API docs.

## Environment Variables

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | OpenAI API key for LLM calls |
| `TAVILY_API_KEY` | Tavily API key for web search |
| `LANGSMITH_API_KEY` | LangSmith tracing key (optional) |
| `LANGSMITH_PROJECT` | LangSmith project name (optional) |
| `LANGSMITH_TRACING` | Enable/disable LangSmith tracing |
| `DATABASE_URL` | Postgres connection string (falls back to SQLite if unset) |
| `ALLOWED_ORIGINS` | Comma-separated list of allowed CORS origins |

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Health check / status message |
| GET | `/health` | Health check |
| POST | `/auth/register` | Register a new user |
| POST | `/auth/login` | Log in and receive a JWT |
| POST | `/research` | Run the research pipeline (streams via SSE) |
| GET | `/download/{filename}` | Download a generated PDF report |

## Deployment

Deployed via Docker on [Render](https://render.com). See `Dockerfile` for the container build. Database hosted on [Neon](https://neon.tech) (Postgres).

To deploy your own instance:
1. Push this repo to GitHub
2. Create a new Web Service on Render, connect the repo (Docker environment auto-detected)
3. Set all environment variables listed above
4. Deploy

## License

MIT 
