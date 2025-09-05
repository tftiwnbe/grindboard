from fastapi import APIRouter, HTTPException, Depends
from typing import Annotated

from app.api.schemas import Task, TaskCreate, TaskUpdate, TokenOut, UserLogin
from app.database import crud, models
from app.dependencies import DBSessionDep
from app.security import hash_password, verify_password, optional_current_user

tasks_router = APIRouter(prefix="/tasks")
auth_router = APIRouter(prefix="/auth", tags=["auth"])


@tasks_router.get("/", response_model=list[Task])
async def tasks_list(
    db: DBSessionDep,
    user: Annotated[models.User | None, Depends(optional_current_user)] = None,
):
    return await crud.get_tasks(db, user)


@tasks_router.post("/", response_model=Task)
async def create_task(
    task: TaskCreate,
    db: DBSessionDep,
    user: Annotated[models.User | None, Depends(optional_current_user)] = None,
):
    return await crud.create_task(db, task, user)


@tasks_router.put("/{id}", response_model=TaskUpdate)
async def update_task(
    id: int,
    task: TaskUpdate,
    db: DBSessionDep,
    user: Annotated[models.User | None, Depends(optional_current_user)] = None,
):
    updated = await crud.update_task(db, task, id, user)
    if not updated:
        raise HTTPException(404, detail="Task not found")
    return updated


@tasks_router.post("/{id}/complete", response_model=Task)
async def complete_task(
    id: int,
    db: DBSessionDep,
    user: Annotated[models.User | None, Depends(optional_current_user)] = None,
):
    completed = await crud.complete_task(db, id, user)
    if not completed:
        raise HTTPException(404, detail="Task not found")
    return completed


@tasks_router.delete("/{id}", response_model=Task)
async def delete_task(
    id: int,
    db: DBSessionDep,
    user: Annotated[models.User | None, Depends(optional_current_user)] = None,
):
    deleted = await crud.delete_task(db, id, user)
    if not deleted:
        raise HTTPException(404, detail="Task not found")
    return deleted


@auth_router.post("/login", response_model=TokenOut)
async def login(payload: UserLogin, db: DBSessionDep):
    user = await crud.get_user_by_username(db, payload.username)
    if not user:
        user = await crud.create_user(
            db,
            username=payload.username,
            password_hash=hash_password(payload.password),
        )
    else:
        if not verify_password(payload.password, user.password_hash):
            raise HTTPException(401, detail="Invalid credentials")
    token = await crud.create_token(db, user)
    return TokenOut(token=token.token)
