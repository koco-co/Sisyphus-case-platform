from app.shared.base_schema import BaseResponse, BaseSchema


class UserCreate(BaseSchema):
    email: str
    username: str
    password: str
    full_name: str | None = None


class UserLogin(BaseSchema):
    username: str
    password: str


class UserResponse(BaseResponse):
    email: str
    username: str
    full_name: str | None
    is_active: bool
    role: str


class TokenResponse(BaseSchema):
    access_token: str
    token_type: str = "bearer"
