from pydantic import BaseModel, ConfigDict, Field


class UserResponse(BaseModel):
    id: int
    username: str
    name: str
    role: str
    email: str | None = None
    phone: str | None = None
    avatar: str | None = None
    status: int

    model_config = ConfigDict(from_attributes = True)

class UserCreateRequest(BaseModel):
    """管理员新增用户时的请求参数"""

    username: str = Field(min_length=3, max_length=20, description="账号")
    password: str = Field(min_length=6, max_length=20, description="密码")
    name: str | None = Field(default=None, max_length=50, description="姓名")
    email: str | None = Field(default=None, max_length=50, description="邮箱")
    phone: str | None = Field(default=None, max_length=20, description="手机号")
    avatar: str | None = Field(default=None, max_length=255, description="头像")
    role: str = Field(default="student", pattern="^(admin|student)$", description="角色：admin/student")
    status: int = Field(default=1, ge=0, le=1, description="状态：1正常 0禁用")


class UserUpdateRequest(BaseModel):
    """修改当前登录用户个人信息，只传需要修改的字段即可"""

    name: str | None = Field(default=None, min_length=1, max_length=50, description="姓名")
    email: str | None = Field(default=None, max_length=50, description="邮箱")
    phone: str | None = Field(default=None, max_length=50, description="手机号")
    avatar: str | None = Field(default=None, max_length=255, description="头像地址")


class UserAdminUpdateRequest(BaseModel):
    """管理员编辑用户时的请求参数，密码留空表示不修改"""

    username: str | None = Field(default=None, min_length=3, max_length=20, description="账号")
    password: str | None = Field(default=None, min_length=6, max_length=20, description="新密码")
    name: str | None = Field(default=None, min_length=1, max_length=50, description="姓名")
    email: str | None = Field(default=None, max_length=50, description="邮箱")
    phone: str | None = Field(default=None, max_length=50, description="手机号")
    avatar: str | None = Field(default=None, max_length=255, description="头像地址")
    role: str | None = Field(default=None, pattern="^(admin|student)$", description="角色：admin/student")
    status: int | None = Field(default=None, ge=0, le=1, description="状态：1正常 0禁用")

class PasswordUpdateRequest(BaseModel):
    """修改密码的请求参数"""
    old_password: str
    new_password: str



