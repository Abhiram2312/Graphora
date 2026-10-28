# Dockerfile for FastAPI backend
FROM python:3.12-slim AS builder
WORKDIR /app
# Install build dependencies
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*
# Install uv (modern Python package manager)
RUN pip install --no-cache-dir uv
# Copy pyproject and install dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen-lockfile --no-dev
# Copy source code
COPY . .
# Runtime image
FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /app /app
EXPOSE 8000
ENV PYTHONUNBUFFERED=1
CMD ["uv", "run", "uvicorn", "apps.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
