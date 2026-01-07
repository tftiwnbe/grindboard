from fastapi import HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import User
from app.core.security import create_access_token, hash_password, verify_password


class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_username(self, username: str) -> User | None:
        stmt = select(User).where(User.username == username)
        return (await self.session.scalars(stmt)).first()

    async def register_or_authenticate(self, username: str, password: str) -> User:
        user = await self.get_by_username(username)
        if not user:
            user = await self._create_user(username, password)
        elif not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )
        return user

    async def _create_user(self, username: str, password: str) -> User:
        user = User(username=username, password_hash=hash_password(password))
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    def issue_token(self, user: User) -> str:
        return create_access_token({"sub": str(user.id)})
