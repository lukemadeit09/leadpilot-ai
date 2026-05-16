# Deployment Guide

This guide targets a practical production stack:

- Frontend: Vercel
- Backend API: Railway or Render
- Database: managed PostgreSQL
- Cache/queue broker: managed Redis

## Production Principles

- Run Alembic migrations before serving API traffic.
- Never commit real `.env` files or provider secrets.
- Keep `APP_ENV=production` for deployed backend services.
- Use exact deployed origins in `CORS_ORIGINS`; do not use `*`.
- Use managed PostgreSQL and Redis for real deployments.
- Use `postgres://` or `postgresql+psycopg://`; the backend normalizes provider `postgres://` URLs for SQLAlchemy.

## Backend Environment

Use `backend/env.production.example` as the provider variable checklist.

Required production values:

```text
APP_ENV=production
DATABASE_URL=postgres://...
REDIS_URL=rediss://...
JWT_SECRET_KEY=<32+ random chars>
CORS_ORIGINS=https://your-frontend.vercel.app
TRUSTED_HOSTS=your-backend.railway.app,your-backend.onrender.com
OPENAI_API_KEY=<optional but required for live AI>
```

The backend fails fast in production if:

- `JWT_SECRET_KEY` is weak or still set to the development default.
- `DATABASE_URL` is not PostgreSQL.
- `CORS_ORIGINS` is empty or contains `*`.

## Railway Backend

1. Create a Railway project.
2. Add PostgreSQL and Redis services.
3. Add the backend service from the repository using `backend/Dockerfile`.
4. Set the backend root directory to `backend` if Railway asks for one.
5. Configure environment variables from `backend/env.production.example`.
6. Set `CORS_ORIGINS` to the Vercel frontend URL.
7. Set `TRUSTED_HOSTS` to the Railway backend hostname.
8. Deploy.

The backend Docker command runs:

```bash
alembic upgrade head && gunicorn app.main:app --worker-class uvicorn.workers.UvicornWorker
```

## Render Backend

1. Create a Web Service from the repository.
2. Use Docker runtime and point Render at `backend/Dockerfile`.
3. Add managed PostgreSQL and Redis.
4. Configure environment variables from `backend/env.production.example`.
5. Set health check path to `/health`.
6. Deploy.

## Vercel Frontend

1. Import the repository into Vercel.
2. Set the root directory to `frontend`.
3. Add this environment variable:

```text
NEXT_PUBLIC_API_URL=https://your-backend-host
```

4. Deploy after the backend URL is known.

The frontend Dockerfile also supports self-hosted deployment by passing `NEXT_PUBLIC_API_URL` as a build argument.

## Production Docker Compose

For production-like self-hosting:

```bash
cp env.production.example env.production
docker compose --env-file env.production -f docker-compose.prod.yml up --build -d
```

Use real secrets in `env.production`; never commit that file.

## Health Checks

- `GET /health`: lightweight process health for load balancers.
- `GET /ready`: checks PostgreSQL and Redis connectivity.

Use `/health` as the container/platform health check. Use `/ready` for operational diagnostics.

## Security Notes

- Containers run as non-root users.
- CORS allows only configured origins.
- Trusted host validation is enabled when `APP_ENV=production`.
- API keys remain backend-only.
- Uploaded files are stored under `UPLOAD_DIR`; use persistent storage or object storage for production.

## Not Included Yet

- Kubernetes manifests
- Stripe billing
- Full observability stack
- Dedicated object storage integration
