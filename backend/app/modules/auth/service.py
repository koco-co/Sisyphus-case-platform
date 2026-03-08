from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash, verify_password
from app.modules.auth.models import User
from app.modules.auth.schemas import TokenResponse, UserCreate


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def register(self, data: UserCreate) -> User:
        user = User(
            email=data.email,
            username=data.username,
            hashed_password=get_password_hash(data.password),
            full_name=data.full_name,
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def authenticate(self, username: str, password: str) -> TokenResponse | None:
        stmt = select(User).where(User.username == username, User.is_active.is_(True))
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        if not user or not verify_password(password, user.hashed_password):
            return None
        token = create_access_token(subject=str(user.id))
        return TokenResponse(access_token=token)

    async def get_by_id(self, user_id: UUID) -> User | None:
        return await self.session.get(User, user_id)
