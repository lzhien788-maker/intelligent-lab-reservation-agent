from sqlalchemy.orm import Session

from app.common.exception import BusinessException
from app.common.response import Response
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, RegisterRequest
from app.schemas.user import UserResponse
from app.utils.jwt import create_access_token
from app.utils.password import verify_password, hash_password


def login(db: Session, data: LoginRequest) -> Response:
    # 1. 根据用户账号查询数据库
    user = db.query(User).filter(User.username == data.username).first()

    # 2. 判断账号和密码是否正确（统一提示，避免泄露账号是否存在）
    if not user or not verify_password(data.password, user.password):
        raise BusinessException(message="账号或密码错误", code=400)

    # 3. 验证账号的状态（1 代表正常）
    if str(user.status) != "1":
        raise BusinessException(message="账号已被禁用", code=403)

    # 4. 创建 token
    token = create_access_token(user.id)

    # 5. 返回 token 和用户信息
    return Response.success(
        message="登录成功",
        data=LoginResponse(token=token, user=UserResponse.model_validate(user)),
    )


def register(db: Session, data: RegisterRequest) -> Response:
    # 1. 两次输入的密码必须一致
    if data.password != data.confirm_password:
        raise BusinessException(message="两次输入的密码不一致", code=400)

    # 2. 判断账号是否已存在
    exists = db.query(User).filter(User.username == data.username).first()
    if exists:
        raise BusinessException(message="该账号已被注册", code=400)

    # 3. 创建用户，密码加密存储
    user = User(
        username=data.username,
        password=hash_password(data.password),
        name=data.username,
        role="student",
        status="1",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return Response.success(message="注册成功")
