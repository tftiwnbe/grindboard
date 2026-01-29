# Stage 1: Build frontend
FROM node:20-alpine AS frontend-build
WORKDIR /app/web
RUN corepack enable
COPY web/pnpm-lock.yaml web/package.json ./
COPY web/pnpm-workspace.yaml ./pnpm-workspace.yaml
RUN pnpm install --frozen-lockfile
COPY web/ .
RUN pnpm build

# Stage 2: Python dependencies
FROM python:3.13-slim AS python-deps
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY server/pyproject.toml ./

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -e .

# Stage 3: Production runtime
FROM python:3.13-slim AS production

# Build arguments for metadata
ARG VERSION=dev
ARG BUILD_DATE
ARG VCS_REF

# OCI Labels
LABEL org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.title="Grindboard" \
      org.opencontainers.image.description="A minimal FastAPI backend for tasks management" \
      org.opencontainers.image.licenses="AGPL-3.0"

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy Python packages from deps stage
COPY --from=python-deps /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=python-deps /usr/local/bin /usr/local/bin

# Copy application code
COPY server/app ./app
COPY server/alembic ./alembic
COPY server/alembic.ini ./

# Copy frontend build
COPY --from=frontend-build /app/web/build ./app/static

# Create data directory
RUN mkdir -p /app/data

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    GRINDBOARD__SERVER__HOST=0.0.0.0

EXPOSE 3000

VOLUME ["/app/data"]

CMD ["python", "-m", "app.main"]
