from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select

from app.database import models
from app.dependencies import DBSessionDep

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 200_000
SALT_BYTES = 16

bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    salt = secrets.token_hex(SALT_BYTES)
    dk = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), ITERATIONS
    )
    return f"{ALGORITHM}${ITERATIONS}${salt}${dk.hex()}"


def verify_password(password: str, hashed: str) -> bool:
    try:
        algo, iters_s, salt, stored_hex = hashed.split("$")
        if algo != ALGORITHM:
            return False
        iters = int(iters_s)
        dk = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt), iters
        )
        return hmac.compare_digest(dk.hex(), stored_hex)
    except Exception:
        return False


def generate_token() -> str:
    return secrets.token_urlsafe(48)


async def get_current_user(
    db: DBSessionDep,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
    ] = None,
) -> models.User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(401, detail="Missing or invalid Authorization header")
    token_value = credentials.credentials

    now = datetime.now(timezone.utc)
    stmt = select(models.AuthToken).where(models.AuthToken.token == token_value)
    token = (await db.scalars(stmt)).first()
    if not token or (
        token.expires_at and token.expires_at.astimezone(timezone.utc) < now
    ):
        raise HTTPException(401, detail="Invalid or expired token")
    user = (
        await db.scalars(select(models.User).where(models.User.id == token.user_id))
    ).first()
    if not user:
        raise HTTPException(401, detail="Invalid user")
    return user


def require_auth(
    user: Annotated[models.User, Depends(get_current_user)],
) -> models.User:
    return user


async def optional_current_user(
    db: DBSessionDep,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
    ] = None,
) -> models.User | None:
    try:
        if credentials is None or credentials.scheme.lower() != "bearer":
            return None
        token_value = credentials.credentials
        now = datetime.now(timezone.utc)
        stmt = select(models.AuthToken).where(models.AuthToken.token == token_value)
        token = (await db.scalars(stmt)).first()
        if not token or (
            token.expires_at and token.expires_at.astimezone(timezone.utc) < now
        ):
            return None
        user = (
            await db.scalars(select(models.User).where(models.User.id == token.user_id))
        ).first()
        return user
    except Exception:
        return None


__all__ = [
    "hash_password",
    "verify_password",
    "get_current_user",
    "bearer_scheme",
    "require_auth",
    "optional_current_user",
]
