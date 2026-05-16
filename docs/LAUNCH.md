# Launch Polish Checklist

LeadPilot AI is structured for portfolio demos, recruiter review, and early customer testing.

## Public Demo Surfaces

- `/`: polished product landing page
- `/pricing`: packaging and usage-aware pricing preview
- `/onboarding`: first-run walkthrough and sample data
- `/register`: workspace creation
- `/dashboard`: operational cockpit after login

## First-Run Path

1. Register a workspace.
2. Open the AI Analyzer.
3. Run the sample inbound email.
4. Review the CRM dashboard.
5. Inspect the created task.
6. Upload a sample knowledge document.
7. Ask a grounded knowledge question.

## Portfolio Review Talking Points

- Monorepo with Next.js frontend and FastAPI backend.
- JWT auth and organization-scoped multi-tenancy.
- Agentic AI workflow that persists lead, analysis, task, and activity log.
- Async jobs with Celery/Redis for AI lead analysis.
- AI usage tracking and quota enforcement.
- RAG knowledge base with document processing and citations.
- Security hardening, CI checks, and observability.

## Before Sharing Publicly

- Capture screenshots using demo data only.
- Confirm `.env` and API keys are not committed.
- Run the full validation suite.
- Add deployment URLs after production hosting is complete.
- Replace placeholder screenshots with actual product images.
