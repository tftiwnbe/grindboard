import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlmodel import select

from app.models import User
from app.config import get_settings
from app.core.dependencies import DBSessionDep

PASSWORD_HASH_SCHEME = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 200_000
PASSWORD_SALT_BYTES = 16

bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    salt = secrets.token_hex(PASSWORD_SALT_BYTES)
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt),
        PASSWORD_ITERATIONS,
    )
    return f"{PASSWORD_HASH_SCHEME}${PASSWORD_ITERATIONS}${salt}${dk.hex()}"


def verify_password(password: str, hashed: str) -> bool:
    try:
        scheme, iters_s, salt, stored_hex = hashed.split("$")
        if scheme != PASSWORD_HASH_SCHEME:
            return False

        dk = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt),
            int(iters_s),
        )
        return hmac.compare_digest(dk.hex(), stored_hex)
    except Exception:
        return False


def create_access_token(claims: dict[str, Any]) -> str:
    settings = get_settings().auth
    to_encode = claims.copy()

    ttl = timedelta(minutes=settings.token_ttl_minutes)
    to_encode["exp"] = datetime.now(timezone.utc) + ttl

    if "sub" in to_encode:
        to_encode["sub"] = str(to_encode["sub"])

    return jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


async def get_current_user(
    db: DBSessionDep,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
    ] = None,
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid Authorization header",
        )

    try:
        settings = get_settings().auth
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid token subject",
            )

        user = (await db.scalars(select(User).where(User.id == int(user_id)))).first()

    except (JWTError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
        )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid user",
        )

    return user


def require_auth(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]

__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "get_current_user",
    "bearer_scheme",
    "require_auth",
    "CurrentUserDep",
]
