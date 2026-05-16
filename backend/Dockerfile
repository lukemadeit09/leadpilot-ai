FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PORT=8000

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --upgrade pip \
    && pip install -r requirements.txt \
    && addgroup --system leadpilot \
    && adduser --system --ingroup leadpilot leadpilot

COPY alembic.ini .
COPY alembic ./alembic
COPY app ./app

RUN mkdir -p /app/uploads \
    && chown -R leadpilot:leadpilot /app

USER leadpilot

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.getenv(\"PORT\", \"8000\")}/health', timeout=3)"

CMD ["sh", "-c", "alembic upgrade head && gunicorn app.main:app --worker-class uvicorn.workers.UvicornWorker --workers ${GUNICORN_WORKERS:-2} --bind 0.0.0.0:${PORT:-8000} --access-logfile - --error-logfile -"]
