# RAG Knowledge Base

Phase 8 upgrades the knowledge base into a production-style retrieval augmented generation system.

## Ingestion Flow

1. User uploads a PDF, text, or markdown file.
2. FastAPI stores the file and creates an `uploaded_documents` record with `pending` status.
3. A Celery worker processes the document in the background.
4. The worker extracts text, chunks content, generates embeddings, and stores chunks.
5. The document status becomes `ready`, or `failed` with an error message.

Tests use `CELERY_TASK_ALWAYS_EAGER=true`, so processing runs synchronously without Redis.

## Storage

- `uploaded_documents`: owner, organization, filename, status, processing error, chunk count, timestamps.
- `knowledge_chunks`: chunk content, source page, token count, embedding model, JSON fallback embedding.
- Alembic migration `20260516_0005_rag_pgvector.py` enables PostgreSQL `vector` extension and adds a `vector(1536)` column plus an IVFFlat cosine index for production pgvector deployments.

The SQLAlchemy model keeps the JSON embedding for local SQLite tests and no-key development while the migration prepares PostgreSQL for pgvector-backed semantic search.

## Retrieval

`POST /knowledge/search` embeds the query, ranks organization-scoped ready chunks by cosine similarity, and returns citation-ready source snippets.

`POST /knowledge/ask` retrieves top chunks, sends the grounded context to the model when OpenAI is configured, and returns:

- answer
- source filenames
- citations with chunk id, document id, filename, snippet, score, and page

Without an OpenAI key, the system uses deterministic local embeddings and a grounded fallback answer so local demos and tests remain reliable.

## Supported Uploads

- `.pdf`
- `.txt`
- `.md`

Other file types are rejected before processing.
