# Async AI Workers

Phase 7 moves lead analysis into a Redis-backed Celery worker queue.

## Runtime Components

- FastAPI enqueues AI lead analysis jobs.
- PostgreSQL stores durable job status in `ai_jobs`.
- Redis acts as Celery broker and result backend.
- A Celery worker executes the existing multi-agent lead workflow.
- The frontend polls job status until the workflow succeeds or fails.

## API Flow

1. `POST /ai/analyze-lead/jobs` creates an `ai_jobs` row and enqueues a Celery task.
2. The worker marks the job `running`.
3. The worker runs analysis, scoring, reply generation, CRM update, task creation, activity logging, and AI usage recording.
4. The worker stores the serialized result on the job and marks it `succeeded`.
5. If final retry fails, the worker stores the error and marks the job `failed`.
6. The frontend polls `GET /ai/jobs/{job_id}`.

## Retry Behavior

Celery retries failed jobs with exponential backoff:

- `max_retries=3`
- `retry_backoff=True`
- `retry_backoff_max=60`
- `retry_jitter=True`

The job table records attempts and final failure messages.

## Local Docker

```bash
docker compose up --build
```

This starts:

- `postgres`
- `redis`
- `backend`
- `worker`
- `frontend`

## Development Tests

Tests set `CELERY_TASK_ALWAYS_EAGER=true` so jobs run synchronously against the pytest database without requiring a live Redis worker.
