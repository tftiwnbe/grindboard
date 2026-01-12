from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.core.database import sessionmanager, run_async_upgrade
from app.tasks.router import router as tasks_router
from app.users.router import router as users_router
from app.tags.router import router as tags_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await run_async_upgrade()
    yield
    if sessionmanager.engine is not None:
        await sessionmanager.close()


settings = get_settings()

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
app.include_router(tags_router)
