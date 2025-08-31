FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1 \
  UV_LINK_MODE=copy \
  PATH="/root/.local/bin:${PATH}"

# Fail-safe shell with pipefail
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Use Debian snapshot to freeze repo versions
RUN echo "deb [check-valid-until=no] http://snapshot.debian.org/archive/debian/20241104T000000Z trixie main" > /etc/apt/sources.list \
  && apt-get update -y \
  && apt-get install -y --no-install-recommends \
  ca-certificates=20250419 \
  curl=8.14.1-2 \
  && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

WORKDIR /app

# Cache deps
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev

# Copy source
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
