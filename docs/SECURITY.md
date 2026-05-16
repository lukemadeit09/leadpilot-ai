# Security Hardening

LeadPilot AI includes a minimal production security baseline for real user and business data.

## Controls

- JWTs include issuer and issued-at claims.
- Production startup rejects the default development JWT secret.
- Auth, AI, billing, and public integration routes have in-memory per-client rate limits.
- Login failures are tracked per user and temporarily lock accounts after repeated failures.
- Security audit logs record sensitive events such as registration, login failures, billing plan changes, API key creation, API key revocation, and public API key usage.
- CORS allows explicit configured origins only and uses explicit methods and headers.
- HTTP responses include security headers such as `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, and HTTPS HSTS.
- Knowledge base uploads validate file extensions, content types, and maximum file size.
- Organization API keys are generated with `secrets`, returned once, and stored only as SHA-256 hashes.
- Public lead intake uses organization API keys and creates leads only inside the authenticated key's organization.

## Environment Variables

- `JWT_SECRET_KEY`: must be a long random value in production.
- `JWT_ISSUER`: expected issuer claim for access tokens.
- `CORS_ORIGINS`: comma-separated frontend origins. Do not use `*` in production.
- `MAX_UPLOAD_BYTES`: maximum upload size for knowledge base documents.
- `RATE_LIMIT_AUTH_PER_MINUTE`: auth endpoint limit per client.
- `RATE_LIMIT_AI_PER_MINUTE`: AI endpoint limit per client.
- `RATE_LIMIT_BILLING_PER_MINUTE`: billing endpoint limit per client.
- `RATE_LIMIT_PUBLIC_PER_MINUTE`: public integration endpoint limit per client.
- `FAILED_LOGIN_LOCK_THRESHOLD`: failed login count before temporary lockout.
- `FAILED_LOGIN_LOCK_MINUTES`: account lockout duration.

## API Keys

Organization owners/admins can create API keys at `POST /integrations/api-keys`. The raw key is shown once in the response. Later list responses only include the key prefix and metadata.

Public integrations submit leads to `POST /integrations/public/leads` with:

```text
X-LeadPilot-Key: lp_live_...
```

Revoked keys are rejected immediately.

## Checks

Run these before production deployment:

```bash
pytest backend
python -m compileall backend\app
bandit -r backend/app
npm audit --omit=dev
```
