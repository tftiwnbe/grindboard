from fastapi import APIRouter, Depends

from app.core.dependencies import DBSessionDep
from app.models import TokenOut, UserLogin
from app.users.service import UserService

router = APIRouter(prefix="/auth", tags=["Auth"])


async def get_service(db: DBSessionDep) -> UserService:
    return UserService(db)


@router.post("/login", response_model=TokenOut)
async def login(payload: UserLogin, service: UserService = Depends(get_service)):
    """Authenticate a user and return an access token."""
    user = await service.register_or_authenticate(
        username=payload.username, password=payload.password
    )
    token = service.issue_token(user)
    return TokenOut(token=token)
