# LeadPilot AI Diagrams

This document captures the system architecture and main runtime flows for LeadPilot AI using Mermaid diagrams that render in GitHub.

## System Architecture

```mermaid
flowchart LR
  subgraph Client["Client Layer"]
    Browser["Browser"]
    NextUI["Next.js App Router UI"]
    ApiClient["Typed API Client"]
  end

  subgraph Backend["FastAPI Backend"]
    FastAPI["FastAPI Application"]
    Auth["JWT Auth Dependency"]
    Routes["Domain Routes"]
    Services["Workflow Services"]
    Agents["AI Agent Layer"]
    Knowledge["Knowledge Service"]
  end

  subgraph Data["Data Layer"]
    Postgres[("PostgreSQL")]
    Redis[("Redis")]
    Uploads["Uploaded File Volume"]
  end

  subgraph External["External Services"]
    OpenAI["OpenAI Chat + Embeddings"]
  end

  Browser --> NextUI
  NextUI --> ApiClient
  ApiClient --> FastAPI
  FastAPI --> Auth
  FastAPI --> Routes
  Routes --> Services
  Services --> Agents
  Services --> Postgres
  Routes --> Knowledge
  Knowledge --> Postgres
  Knowledge --> Uploads
  Agents --> OpenAI
  Knowledge --> OpenAI
  FastAPI -. "future cache/jobs" .-> Redis
```

## Backend Module Architecture

```mermaid
flowchart TB
  Main["app/main.py"] --> Middleware["CORS + Startup"]
  Main --> AuthRoutes["routes/auth.py"]
  Main --> LeadRoutes["routes/leads.py"]
  Main --> AIRoutes["routes/ai.py"]
  Main --> TaskRoutes["routes/tasks.py"]
  Main --> KnowledgeRoutes["routes/knowledge.py"]
  Main --> ActivityRoutes["routes/activity.py"]

  AuthRoutes --> Security["auth/security.py"]
  LeadRoutes --> Models["models/core.py"]
  TaskRoutes --> Models
  ActivityRoutes --> Models
  AIRoutes --> Workflow["services/ai_workflow.py"]
  KnowledgeRoutes --> KnowledgeService["services/knowledge.py"]

  Workflow --> Analyzer["AnalyzerAgent"]
  Workflow --> Scoring["ScoringAgent"]
  Workflow --> Reply["ReplyAgent"]
  Workflow --> CRM["CRMAgent"]
  Workflow --> TaskAgent["TaskAgent"]
  Workflow --> ActivityService["services/activity.py"]
  Workflow --> Models
  KnowledgeService --> Models
```

## Deployment Architecture

```mermaid
flowchart LR
  User["User Browser"] --> Frontend["frontend container\nNext.js"]
  Frontend --> Backend["backend container\nFastAPI + Uvicorn"]
  Backend --> Postgres[("postgres container\nPostgreSQL 16")]
  Backend --> Redis[("redis container\nRedis 7")]
  Backend --> Volume["backend_uploads volume"]
  Backend --> OpenAI["OpenAI API"]

  Compose["docker-compose.yml"] --> Frontend
  Compose --> Backend
  Compose --> Postgres
  Compose --> Redis
```

## Authentication Sequence

```mermaid
sequenceDiagram
  autonumber
  actor User
  participant UI as Next.js UI
  participant API as FastAPI /auth
  participant DB as PostgreSQL

  User->>UI: Submit register or login form
  UI->>API: POST /auth/register or /auth/login
  API->>DB: Find or create user
  DB-->>API: User record
  API->>API: Hash or verify password
  API->>API: Sign JWT with user id in sub claim
  API-->>UI: access_token + user
  UI->>UI: Store token in localStorage
  UI-->>User: Redirect to dashboard
```

## Protected Request Sequence

```mermaid
sequenceDiagram
  autonumber
  actor User
  participant UI as Next.js Page
  participant Client as frontend/lib/api.ts
  participant API as FastAPI Route
  participant Auth as get_current_user
  participant DB as PostgreSQL

  User->>UI: Open protected dashboard route
  UI->>Client: Request data
  Client->>Client: Read JWT from localStorage
  Client->>API: GET /dashboard/metrics with Bearer token
  API->>Auth: Resolve current user
  Auth->>Auth: Decode and validate JWT
  Auth->>DB: Load active user by id
  DB-->>Auth: User
  API->>DB: Query tenant-scoped CRM data
  DB-->>API: Leads, tasks, activity
  API-->>Client: JSON response
  Client-->>UI: Typed data
  UI-->>User: Render dashboard
```

## AI Lead Analysis Lifecycle

```mermaid
sequenceDiagram
  autonumber
  actor Rep as Sales Rep
  participant UI as AI Analyzer Page
  participant API as POST /ai/analyze-lead
  participant Workflow as AILeadWorkflow
  participant Analyzer as AnalyzerAgent
  participant Scoring as ScoringAgent
  participant Reply as ReplyAgent
  participant CRM as CRMAgent
  participant Tasker as TaskAgent
  participant DB as PostgreSQL
  participant OpenAI as OpenAI API

  Rep->>UI: Paste customer message
  UI->>API: Submit lead analysis payload
  API->>Workflow: run(db, user, payload)
  Workflow->>Analyzer: analyze(message)
  Analyzer->>OpenAI: Structured JSON prompt if API key exists
  OpenAI-->>Analyzer: Summary, sentiment, urgency, category
  Analyzer-->>Workflow: Analysis fields
  Workflow->>Scoring: score(message, analysis)
  Scoring-->>Workflow: Lead score
  Workflow->>Reply: draft(message, analysis)
  Reply-->>Workflow: Suggested reply
  Workflow->>CRM: decide(analysis)
  CRM-->>Workflow: Pipeline status + recommended action
  Workflow->>Tasker: create_task(message, analysis)
  Tasker-->>Workflow: Follow-up task spec
  Workflow->>DB: Upsert lead
  Workflow->>DB: Insert lead analysis
  Workflow->>DB: Insert task
  Workflow->>DB: Insert activity log
  DB-->>Workflow: Persisted records
  Workflow-->>API: Lead, analysis, task, activity
  API-->>UI: AnalyzeLeadResponse
  UI-->>Rep: Show score, summary, reply, task
```

## Knowledge Base RAG Sequence

```mermaid
sequenceDiagram
  autonumber
  actor Rep as Sales Rep
  participant UI as Knowledge Page
  participant API as Knowledge Routes
  participant Service as KnowledgeService
  participant Files as Upload Volume
  participant DB as PostgreSQL
  participant OpenAI as OpenAI API

  Rep->>UI: Upload PDF or text document
  UI->>API: POST /knowledge/upload
  API->>Service: upload(db, user, file)
  Service->>Files: Store uploaded file
  Service->>Service: Extract text
  Service->>Service: Chunk text
  Service->>OpenAI: Create embeddings if API key exists
  OpenAI-->>Service: Embedding vectors
  Service->>DB: Store uploaded_document and knowledge_chunks
  API-->>UI: Document metadata

  Rep->>UI: Ask company knowledge question
  UI->>API: POST /knowledge/ask
  API->>Service: answer(db, user_id, question)
  Service->>DB: Load tenant-scoped chunks
  Service->>OpenAI: Embed question if API key exists
  Service->>Service: Rank chunks by vector or keyword similarity
  Service->>OpenAI: Generate grounded answer if API key exists
  OpenAI-->>Service: Answer
  API-->>UI: Answer + sources
  UI-->>Rep: Render grounded response
```

## Multi-Tenant Data Isolation

```mermaid
flowchart TB
  UserA["User A JWT"] --> AuthA["current_user.id = A"]
  UserB["User B JWT"] --> AuthB["current_user.id = B"]

  AuthA --> QueryA["WHERE owner_id = A"]
  AuthB --> QueryB["WHERE owner_id = B"]

  QueryA --> LeadsA["User A leads"]
  QueryA --> TasksA["User A tasks"]
  QueryA --> DocsA["User A documents"]
  QueryA --> ActivityA["User A activity"]

  QueryB --> LeadsB["User B leads"]
  QueryB --> TasksB["User B tasks"]
  QueryB --> DocsB["User B documents"]
  QueryB --> ActivityB["User B activity"]

  QueryA -. "cannot read" .-> LeadsB
  QueryB -. "cannot read" .-> LeadsA
```

## Future Celery and Redis Workflow

Redis exists in the Docker stack today as infrastructure for caching and future background processing. Celery is not implemented yet, but this is the intended production evolution:

```mermaid
sequenceDiagram
  autonumber
  actor Rep as Sales Rep
  participant UI as Next.js UI
  participant API as FastAPI
  participant Redis as Redis Broker
  participant Celery as Celery Worker
  participant DB as PostgreSQL
  participant OpenAI as OpenAI API

  Rep->>UI: Upload large document
  UI->>API: POST /knowledge/upload
  API->>DB: Create uploaded_document with processing status
  API->>Redis: Enqueue document_ingestion job
  API-->>UI: Accepted response
  Celery->>Redis: Pull job
  Celery->>DB: Load document metadata
  Celery->>Celery: Extract and chunk text
  Celery->>OpenAI: Generate embeddings
  Celery->>DB: Save knowledge chunks and mark processed
  UI->>API: Poll or subscribe to status
  API-->>UI: Processing complete
```
