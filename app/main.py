from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from app.api.routers import router
from app.config import settings
from app.database import sessionmanager


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield
    if sessionmanager.engine is not None:
        await sessionmanager.close()


app = FastAPI(lifespan=lifespan, title=settings.project_name)
app.include_router(router)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        reload=True,
        port=8000,
    )
