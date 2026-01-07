from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.core.database import sessionmanager
from app.tasks.router import router as tasks_router
from app.users.router import router as users_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield
    if sessionmanager.engine is not None:
        await sessionmanager.close()


settings = get_settings()
if not settings.app.config_path.exists():
    settings.save_settings()

app = FastAPI(lifespan=lifespan, title=settings.app.project_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.app.cors_allow_origins,
    allow_methods=settings.app.cors_allow_methods,
    allow_headers=settings.app.cors_allow_headers,
    allow_credentials=settings.app.cors_allow_credentials,
)
app.include_router(users_router)
app.include_router(tasks_router)


if __name__ == "__main__":
    uvicorn.run("app.main:app", host=settings.server.host, port=settings.server.port)
