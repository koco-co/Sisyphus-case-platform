from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, get_password_hash, verify_password
from app.modules.auth.models import User
from app.modules.auth.schemas import TokenResponse, UserCreate, UserResponse


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def register(self, data: UserCreate) -> User:
        try:
            hashed_password = get_password_hash(data.password)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

        user = User(
            email=data.email,
            username=data.username,
            hashed_password=hashed_password,
            full_name=data.full_name,
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def authenticate(self, username: str, password: str) -> TokenResponse | None:
        stmt = select(User).where(
            User.username == username,
            User.is_active.is_(True),
            User.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        if not user or user.deleted_at is not None or not verify_password(password, user.hashed_password):
            return None
        token = create_access_token(subject=str(user.id))
        return TokenResponse(access_token=token, user=UserResponse.model_validate(user))

    async def get_by_id(self, user_id: UUID) -> User | None:
        user = await self.session.get(User, user_id)
        if not user or user.deleted_at is not None:
            return None
        return user
