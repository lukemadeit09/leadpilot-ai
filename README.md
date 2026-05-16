# LeadPilot AI

LeadPilot AI is an AI-powered CRM automation platform that reads customer messages, analyzes leads, generates replies, saves data to a CRM, creates follow-up tasks, and helps sales teams work faster.

## Product Summary

LeadPilot AI demonstrates a production-style B2B SaaS workflow: a sales rep submits an inbound email, the backend runs an agentic AI workflow, the CRM pipeline is updated, a follow-up task is created, and the dashboard reflects the operational state.

## Features

- JWT authentication with register, login, and current-user endpoints
- CRM lead management with status tracking, search, filtering, scoring, and lead detail views
- AI email analyzer with structured output for summary, sentiment, urgency, category, score, buying intent, reply, and follow-up task
- Multi-agent backend design: analyzer, scoring, reply, CRM, and task agents
- Agentic workflow that persists lead, analysis, task, and activity log in one transaction
- RAG-style knowledge base with PDF/text uploads, chunking, embeddings when OpenAI is configured, and fallback local search
- Dashboard metrics, pipeline chart, activity timeline, task queue, and modern dark SaaS UI
- Dockerized frontend, backend, PostgreSQL, and Redis
- Environment-variable based configuration with no committed secrets

## Tech Stack

- Frontend: Next.js, TypeScript, Tailwind CSS, Recharts, Lucide icons
- Backend: FastAPI, SQLAlchemy, Pydantic, PostgreSQL, JWT auth
- AI: OpenAI API, structured JSON outputs, embeddings for document search
- Infrastructure: Docker, Docker Compose, Redis-ready service configuration

## Architecture

```mermaid
flowchart LR
  UI[Next.js SaaS Dashboard] --> API[FastAPI]
  API --> Auth[JWT Auth]
  API --> CRM[CRM Workflow Services]
  CRM --> DB[(PostgreSQL)]
  API --> Agents[AI Agents]
  Agents --> OpenAI[OpenAI API]
  API --> KB[RAG Knowledge Base]
  KB --> DB
  API --> Redis[(Redis)]
```

More detail is available in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Folder Structure

```text
leadpilot-ai/
  backend/
    app/
      agents/
      auth/
      models/
      routes/
      schemas/
      services/
  frontend/
    app/
    components/
    hooks/
    lib/
    types/
  docs/
  docker-compose.yml
  .env.example
```

## Local Setup

1. Create a local env file:

```bash
cp .env.example .env
```

2. Set `JWT_SECRET_KEY` to a long random value.

3. Optional: set `OPENAI_API_KEY` to enable live model calls. Without it, the backend uses deterministic demo fallbacks so the app still runs locally.

4. Start the full stack:

```bash
docker compose up --build
```

5. Open the app:

```text
Frontend: http://localhost:3000
Backend API: http://localhost:8000
API docs: http://localhost:8000/docs
```

## Manual Development

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend tests:

```bash
cd backend
.venv\Scripts\activate
pip install -r requirements-dev.txt
cd ..
pytest
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `JWT_SECRET_KEY`: signing secret for access tokens
- `ACCESS_TOKEN_EXPIRE_MINUTES`: access token lifetime
- `OPENAI_API_KEY`: optional OpenAI API key
- `OPENAI_MODEL`: chat model for AI agents
- `OPENAI_EMBEDDING_MODEL`: embedding model for document chunks
- `CORS_ORIGINS`: comma-separated frontend origins
- `NEXT_PUBLIC_API_URL`: browser-facing backend URL

## API Overview

- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `GET /dashboard/metrics`
- `GET /leads`
- `POST /leads`
- `GET /leads/{id}`
- `PATCH /leads/{id}`
- `DELETE /leads/{id}`
- `POST /ai/analyze-lead`
- `POST /ai/generate-reply`
- `GET /tasks`
- `POST /tasks`
- `PATCH /tasks/{id}`
- `DELETE /tasks/{id}`
- `POST /knowledge/upload`
- `GET /knowledge/documents`
- `POST /knowledge/ask`
- `GET /activity`

## Screenshots

Add screenshots here after running the app locally:

- Landing page
- Dashboard
- AI analyzer workflow
- Leads table
- Knowledge base

## Portfolio Notes

This project is structured to demonstrate practical AI automation engineering: multi-step business workflows, backend orchestration, database persistence, secure auth, AI agent boundaries, RAG ingestion, and a recruiter-friendly SaaS interface.

## Future Improvements

- Add Alembic migrations for production schema evolution
- Add Celery workers for long-running document ingestion
- Add Redis-backed caching for dashboard metrics and knowledge search
- Add WebSocket activity streaming to the dashboard
- Add role-based admin controls and organization workspaces
- Add email sending provider integration for approved AI replies
