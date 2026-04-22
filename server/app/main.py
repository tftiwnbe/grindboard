import uvicorn
from contextlib import asynccontextmanager
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.core.database import sessionmanager, run_async_upgrade
from app.core.limiter import limiter
from app.tasks.router import router as tasks_router
from app.users.router import router as users_router
from app.tags.router import router as tags_router
from app.web.router import router as web_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    settings = get_settings()
    settings.app.data_dir.mkdir(parents=True, exist_ok=True)
    await run_async_upgrade()
    yield
    if sessionmanager.engine is not None:
        await sessionmanager.close()


settings = get_settings()

app = FastAPI(lifespan=lifespan, title=settings.app.project_name)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.app.cors_allow_origins,
    allow_origin_regex=settings.app.cors_allow_origin_regex,
    allow_methods=settings.app.cors_allow_methods,
    allow_headers=settings.app.cors_allow_headers,
    allow_credentials=settings.app.cors_allow_credentials,
)


_SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=()",
}


@app.middleware("http")
async def add_security_headers(request: Request, call_next: Callable) -> Response:
    response = await call_next(request)
    for header, value in _SECURITY_HEADERS.items():
        response.headers[header] = value
    return response


app.include_router(users_router, prefix="/api/v1")
app.include_router(tasks_router, prefix="/api/v1")
app.include_router(tags_router, prefix="/api/v1")
app.include_router(web_router)

if __name__ == "__main__":
    uvicorn.run(
        app="app.main:app",
        host=settings.server.host,
        port=settings.server.port,
    )
