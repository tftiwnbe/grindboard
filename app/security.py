from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated

from jose import JWTError, jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select

from app.config import settings
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


def create_access_token(claims: dict[str, str | int]) -> str:
    to_encode = claims.copy()
    ttl = timedelta(minutes=settings.token_ttl_minutes)
    to_encode["exp"] = datetime.now(timezone.utc) + ttl
    return jwt.encode(
        to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )


async def get_current_user(
    db: DBSessionDep,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
    ] = None,
) -> models.User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(401, detail="Missing or invalid Authorization header")
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(401, detail="Invalid token subject")
        user = (
            await db.scalars(select(models.User).where(models.User.id == int(user_id)))
        ).first()
    except (JWTError, ValueError):
        raise HTTPException(401, detail="Invalid or expired token")

    if not user:
        raise HTTPException(401, detail="Invalid user")
    return user


def require_auth(
    user: Annotated[models.User, Depends(get_current_user)],
) -> models.User:
    return user


__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "get_current_user",
    "bearer_scheme",
    "require_auth",
]
