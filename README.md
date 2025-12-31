# Grindboard API

A minimal, async FastAPI backend for managing tasks.

## Features

- Task CRUD: create, list, update, delete tasks
- Async SQLAlchemy sessions with dependency injection
- Alembic migrations for schema evolution
- Typed Pydantic v2 schemas with `from_attributes`
- Test suite with per-test database isolation

## Tech Stack

- FastAPI (async) + Starlette tooling
- SQLAlchemy 2.0 (async) + aiosqlite (SQLite)
- Alembic migrations
- Pydantic v2 / pydantic-settings
- Pytest (+ TestClient) for integration-style tests

## Quick Start

### Prerequisites

- Python 3.13+
- Optional: [`uv`](https://github.com/astral-sh/uv) for fast installs (Makefile uses it). If you don't have `uv`, you can substitute `pip`.

### Setup

```bash
# Create venv and install dev deps (uses uv if available)
make install

# Start the app in dev mode (reload)
make start
# or run directly with uvicorn
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The app reads configuration from environment variables via `.env` at the repo root.

Example `.env`:

```env
# Human-friendly name for OpenAPI docs
PROJECT_NAME=Grindboard

# SQLite URL
DATABASE_URL=sqlite+aiosqlite:///./tasks.db

# SQLAlchemy echo and log level
ECHO_SQL=false
LOG_LEVEL=INFO
```

## API

Base path: `/tasks`

- `GET /tasks/` → list all tasks (returns `list[Task]`)
- `POST /tasks/` → create a task (returns created `Task`, HTTP 200 currently)
- `PUT /tasks/{id}` → update task title/description (returns `TaskUpdate`, i.e., only updated fields)
- `POST /tasks/{id}/complete` → toggle completion (returns full `Task`)
- `DELETE /tasks/{id}` → delete task (returns deleted `Task`)

Well..

- Create responds with 200 OK (not 201) in the current implementation.
- `PUT /tasks/{id}` responds with partial fields (per `TaskUpdate`), not the full `Task`.
- The complete endpoint toggles the `completed` flag; it is not idempotent.

## Authentication (optional)

- Enable auth by setting `AUTH_ENABLED=true` in `.env`. When enabled, all `/tasks` routes require a `Bearer` token (FastAPI security: HTTPBearer).
- Token lifetime is configurable via `TOKEN_TTL_MINUTES` (default 1440 minutes).
- Sessions: by default, a new login invalidates previous tokens (single-session). To allow multiple concurrent logins per user, set `MAX_TOKENS_PER_USER` to a number greater than 1.
  - Expired tokens are cleaned up opportunistically on login.

### Endpoint

- `POST /auth/login` — body: `{ "username": "alice", "password": "secret123" }`
  - If the user does not exist, it is created and a token is issued.
  - If the user exists, credentials are verified and a token is issued.
  - Response: `{ "token": "..." }`

## Migrations

```bash
# Upgrade to latest
uv run alembic upgrade head

# Create a new migration after model changes
uv run alembic revision --autogenerate -m "your message"

# Downgrade one step
uv run alembic downgrade -1
```

## Deploy (GH Actions)

- Container image builds to `ghcr.io/tftiwnbe/grindboard` on pushes to `main` and tags `v*`.
- The workflow SSHes to server and runs Docker Compose in `~/grindboard`.

GitHub repository secrets (Settings → Secrets and variables → Actions):

- Environment - production
- `DEPLOY_HOST`: your server IP/host
- `DEPLOY_USER`: SSH user (must be in `docker` group)
- `DEPLOY_SSH_KEY`: private key for that user (PEM)
- `DEPLOY_SSH_KEY_PASSPHRASE` (optional): passphrase if the key is protected
- `GHCR_USER` and `GHCR_PAT` (optional): only if your GHCR image is private; skip if public

Deploy flow:

- On push to `main` or creating a `v*` tag: builds and pushes `ghcr.io/tftiwnbe/grindboard`.
- Then copies `deploy/compose.yml` to `~/grindboard/compose.yml` and runs:
  - pull latest image
  - run `alembic upgrade head`
  - start/update the service with restart policy

Environment for production is hardcoded in `deploy/compose.yml`.

Service runs on `:8000` by default. Put a reverse proxy in front if needed.
