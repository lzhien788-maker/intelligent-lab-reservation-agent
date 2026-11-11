from pydantic import BaseModel, Field

from app.schemas.user import UserResponse


class LoginRequest(BaseModel):
    """登录请求参数"""

    username: str = Field(min_length=3, max_length=20, description="账号")
    password: str = Field(min_length=6, max_length=20, description="密码")


class LoginResponse(BaseModel):
    """登录成功返回的数据"""

    token: str
    user: UserResponse


class RegisterRequest(BaseModel):
    """注册请求参数"""

    username: str = Field(min_length=3, max_length=20, description="账号")
    password: str = Field(min_length=6, max_length=20, description="密码")
    confirm_password: str = Field(min_length=6, max_length=20, description="确认密码")
