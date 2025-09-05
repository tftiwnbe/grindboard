from contextlib import asynccontextmanager

import uvicorn
from fastapi import Depends, FastAPI

from app.api.routers import auth_router, tasks_router
from app.config import settings
from app.database import sessionmanager
from app.security import require_auth


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield
    if sessionmanager.engine is not None:
        await sessionmanager.close()


app = FastAPI(lifespan=lifespan, title=settings.project_name)

app.include_router(auth_router)
if settings.auth_enabled:
    app.include_router(tasks_router, dependencies=[Depends(require_auth)])
else:
    app.include_router(tasks_router)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        reload=True,
        port=8000,
    )
