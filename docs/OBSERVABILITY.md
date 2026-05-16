# Observability and Monitoring

LeadPilot AI includes a lightweight monitoring baseline that works locally without external services and can be connected to Sentry in production.

## Backend Logging

The FastAPI backend emits structured JSON logs to stdout. Request logs include:

- request id
- method
- path
- status code
- duration in milliseconds
- client IP
- error type for unhandled exceptions

The request logger never records request bodies, response bodies, authorization headers, cookies, JWTs, API keys, passwords, or customer message content.

## Health Endpoints

- `GET /health`: basic service metadata and status.
- `GET /live`: liveness probe for process uptime checks.
- `GET /ready`: readiness probe that verifies database connectivity.

Use `/live` for container liveness checks and `/ready` for load balancer readiness checks.

## Backend Sentry

Backend Sentry is optional. If `SENTRY_DSN` is unset, the app runs without Sentry.

Environment variables:

- `SENTRY_DSN`: backend Sentry DSN.
- `SENTRY_TRACES_SAMPLE_RATE`: backend tracing sample rate, default `0`.
- `APP_ENV`: Sentry environment name.

## Frontend Sentry

Frontend Sentry is optional. If `NEXT_PUBLIC_SENTRY_DSN` is unset, the frontend runs without client-side Sentry.

Environment variables:

- `NEXT_PUBLIC_SENTRY_DSN`: browser-safe Sentry DSN.
- `NEXT_PUBLIC_SENTRY_TRACES_SAMPLE_RATE`: frontend tracing sample rate, default `0`.
- `NEXT_PUBLIC_APP_ENV`: frontend environment name.
- `SENTRY_ORG`, `SENTRY_PROJECT`, `SENTRY_AUTH_TOKEN`: optional build-time upload configuration for source maps. Do not commit these values.

## Privacy Notes

Keep logs operational. Do not add request body logging for CRM messages, knowledge base documents, uploaded file content, JWTs, passwords, API keys, or billing data.
