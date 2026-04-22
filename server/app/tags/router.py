from fastapi import APIRouter, Depends, HTTPException, Query, Response

from app.core.dependencies import DBSessionDep
from app.core.security import CurrentUserDep
from app.models import TagRead
from app.tags.service import TagService

router = APIRouter(prefix="/tags", tags=["Tags"])


async def get_service(db: DBSessionDep) -> TagService:
    return TagService(db)


@router.get("/", response_model=list[TagRead])
async def list_tags(
    current_user: CurrentUserDep,
    service: TagService = Depends(get_service),
):
    """List all tags for the current user."""
    return await service.list(current_user)


@router.post("/", response_model=TagRead)
async def create_tag(
    current_user: CurrentUserDep,
    service: TagService = Depends(get_service),
    name: str = Query(min_length=1, max_length=50),
):
    """Create a new tag."""
    return await service.create(current_user, name)


@router.put("/{tag_id}", response_model=TagRead)
async def rename_tag(
    tag_id: int,
    current_user: CurrentUserDep,
    service: TagService = Depends(get_service),
    name: str = Query(min_length=1, max_length=50),
):
    """Rename a tag."""
    tag = await service.rename(tag_id, current_user, name)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag


@router.delete("/{tag_id}", status_code=204, response_model=None)
async def delete_tag(
    tag_id: int,
    current_user: CurrentUserDep,
    service: TagService = Depends(get_service),
):
    """Delete a tag and remove it from all associated tasks."""
    success = await service.delete(tag_id, current_user)
    if not success:
        raise HTTPException(status_code=404, detail="Tag not found")
    return Response(status_code=204)
