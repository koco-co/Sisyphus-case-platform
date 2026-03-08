from fastapi import APIRouter, HTTPException, status

from app.core.dependencies import AsyncSessionDep
from app.modules.auth.schemas import TokenResponse, UserCreate, UserLogin, UserResponse
from app.modules.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, session: AsyncSessionDep) -> UserResponse:
    service = AuthService(session)
    user = await service.register(data)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, session: AsyncSessionDep) -> TokenResponse:
    service = AuthService(session)
    result = await service.authenticate(data.username, data.password)
    if not result:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return result
