FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY app ./app
RUN apt-get update \
    && apt-get install --no-install-recommends --yes docker-cli \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --upgrade pip \
    && pip install ".[dev]"

COPY tests ./tests
COPY experiments ./experiments
COPY migrations ./migrations
COPY alembic.ini ./alembic.ini

RUN mkdir -p /app/artifacts

EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
