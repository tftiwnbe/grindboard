from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import DBSessionDep
from app.core.security import CurrentUserDep
from app.models import TaskCreate, TaskRead, TaskUpdate
from app.tasks.service import TaskService

router = APIRouter(prefix="/tasks", tags=["Tasks"])


async def get_service(db: DBSessionDep) -> TaskService:
    return TaskService(db)


@router.get("/", response_model=list[TaskRead])
async def list_tasks(
    current_user: CurrentUserDep,
    service: TaskService = Depends(get_service),
):
    """List all tasks for the current user, ordered by position."""
    return await service.list(current_user)


@router.post("/", response_model=TaskRead)
async def create_task(
    task_data: TaskCreate,
    current_user: CurrentUserDep,
    service: TaskService = Depends(get_service),
):
    """Create a new task at the end of the user's list."""
    return await service.create(current_user, task_data)


@router.put("/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    current_user: CurrentUserDep,
    service: TaskService = Depends(get_service),
):
    """Update a task's details."""
    task = await service.update(task_id, current_user, task_data)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/{task_id}/complete", response_model=TaskRead)
async def toggle_task(
    task_id: int,
    current_user: CurrentUserDep,
    service: TaskService = Depends(get_service),
):
    """Toggle the completed status of a task."""
    task = await service.toggle_complete(task_id, current_user)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.delete("/{task_id}", response_model=TaskRead)
async def delete_task(
    task_id: int,
    current_user: CurrentUserDep,
    service: TaskService = Depends(get_service),
):
    """Delete a task."""
    task = await service.delete(task_id, current_user)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/{task_id}/move", response_model=TaskRead)
async def move_task(
    task_id: int,
    current_user: CurrentUserDep,
    service: TaskService = Depends(get_service),
    after_id: int | None = None,
):
    """
    Move a task to a new position:
    - If after_id is None → move to top
    - Otherwise → move after the task with after_id
    """
    task = await service.move_task(task_id, current_user, after_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
