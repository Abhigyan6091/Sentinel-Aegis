FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Runtime dependencies only: test and lint tooling has no place in a production image.
COPY pyproject.toml ./
COPY app ./app
RUN pip install --no-cache-dir --prefix=/install "."


FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Non-root by default so the image matches the Kubernetes securityContext.
RUN groupadd --gid 10001 aegis \
    && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin aegis

WORKDIR /app

COPY --from=builder /install /usr/local
COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app
COPY regression ./regression

USER 10001:10001

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).status == 200 else 1)"

# Migrations run here for docker-compose; Kubernetes uses a dedicated init container.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
