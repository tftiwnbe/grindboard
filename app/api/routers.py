from fastapi import APIRouter, HTTPException

from app.api.dependencies import DBSessionDep
from app.api.schemas import Task, TaskCreate, TaskUpdate
from app.database import crud

router = APIRouter(
    prefix="/tasks",
)


@router.get("/", response_model=list[Task])
async def tasks_list(db: DBSessionDep):
    return await crud.get_tasks(db)


@router.post("/", response_model=Task)
async def create_task(task: TaskCreate, db: DBSessionDep):
    return await crud.create_task(db, task)


@router.put("/{id}", response_model=TaskUpdate)
async def update_task(id: int, task: TaskUpdate, db: DBSessionDep):
    updated = await crud.update_task(db, task, id)
    if not updated:
        raise HTTPException(404, detail="Task not found")
    return updated


@router.post("/{id}/complete", response_model=Task)
async def complete_task(id: int, db: DBSessionDep):
    completed = await crud.complete_task(db, id)
    if not completed:
        raise HTTPException(404, detail="Task not found")
    return completed


@router.delete("/{id}", response_model=Task)
async def delete_task(id: int, db: DBSessionDep):
    deleted = await crud.delete_task(db, id)
    if not deleted:
        raise HTTPException(404, detail="Task not found")
    return deleted
