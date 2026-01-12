from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import DBSessionDep
from app.core.security import CurrentUserDep
from app.models import Tag
from app.tags.service import TagService

router = APIRouter(prefix="/tags", tags=["Tags"])


async def get_service(db: DBSessionDep) -> TagService:
    return TagService(db)


@router.get("/", response_model=list[Tag])
async def list_tags(
    current_user: CurrentUserDep,
    service: TagService = Depends(get_service),
):
    """List all tags for the current user."""
    return await service.list(current_user)


@router.post("/", response_model=Tag)
async def create_tag(
    name: str,
    current_user: CurrentUserDep,
    service: TagService = Depends(get_service),
):
    """Create a new tag."""
    return await service.create(current_user, name)


@router.put("/{tag_id}", response_model=Tag)
async def rename_tag(
    tag_id: int,
    name: str,
    current_user: CurrentUserDep,
    service: TagService = Depends(get_service),
):
    """Rename a tag."""
    tag = await service.rename(tag_id, current_user, name)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag


@router.delete("/{tag_id}")
async def delete_tag(
    tag_id: int,
    current_user: CurrentUserDep,
    service: TagService = Depends(get_service),
):
    """Delete a tag and remove it from all associated tasks."""
    success = await service.delete(tag_id, current_user)
    if not success:
        raise HTTPException(status_code=404, detail="Tag not found")
    return {"message": "Tag deleted successfully"}


@router.post("/tasks/{task_id}/tags/{tag_id}", response_model=Tag)
async def add_tag_to_task(
    task_id: int,
    tag_id: int,
    current_user: CurrentUserDep,
    service: TagService = Depends(get_service),
):
    """Add an existing tag to a task."""
    tag = await service.add_tag_to_task(task_id, tag_id, current_user)
    if not tag:
        raise HTTPException(status_code=404, detail="Task or tag not found")
    return tag


@router.delete("/tasks/{task_id}/tags/{tag_id}")
async def remove_tag_from_task(
    task_id: int,
    tag_id: int,
    current_user: CurrentUserDep,
    service: TagService = Depends(get_service),
):
    """Remove a tag from a task."""
    success = await service.remove_tag_from_task(task_id, tag_id, current_user)
    if not success:
        raise HTTPException(status_code=404, detail="Task or tag not found")
    return {"message": "Tag removed from task"}


@router.post("/tasks/{task_id}/tags", response_model=Tag)
async def create_and_add_tag(
    task_id: int,
    name: str,
    current_user: CurrentUserDep,
    service: TagService = Depends(get_service),
):
    """Create a new tag and immediately add it to a task."""
    tag = await service.create_and_add_to_task(task_id, current_user, name)
    if not tag:
        raise HTTPException(status_code=404, detail="Task not found")
    return tag
