from typing import Annotated

import jwt
from fastapi import APIRouter, Depends, Request, Response
from fastapi.security import HTTPAuthorizationCredentials

from app.config import get_settings
from app.core.dependencies import DBSessionDep
from app.core.limiter import limiter
from app.core.security import bearer_scheme, revoke_token
from app.models import TokenOut, UserLogin
from app.users.service import UserService

router = APIRouter(prefix="/auth", tags=["Auth"])


async def get_service(db: DBSessionDep) -> UserService:
    return UserService(db)


@router.post("/register", response_model=TokenOut, status_code=201)
@limiter.limit("10/minute")
async def register(
    request: Request,
    payload: UserLogin,
    service: UserService = Depends(get_service),
):
    """Register a new user and return an access token."""
    user = await service.register(username=payload.username, password=payload.password)
    token = service.issue_token(user)
    return TokenOut(token=token)


@router.post("/login", response_model=TokenOut)
@limiter.limit("10/minute")
async def login(
    request: Request,
    payload: UserLogin,
    service: UserService = Depends(get_service),
):
    """Authenticate an existing user and return an access token."""
    user = await service.authenticate(username=payload.username, password=payload.password)
    token = service.issue_token(user)
    return TokenOut(token=token)


@router.post("/logout", status_code=204, response_model=None)
async def logout(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
    ] = None,
):
    """Invalidate the current access token."""
    if credentials:
        try:
            settings = get_settings().auth
            payload = jwt.decode(
                credentials.credentials,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm],
            )
            jti = payload.get("jti")
            if jti:
                revoke_token(jti)
        except Exception:
            pass
    return Response(status_code=204)
