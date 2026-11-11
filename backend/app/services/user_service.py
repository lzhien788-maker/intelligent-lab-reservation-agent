from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.common.exception import BusinessException
from app.common.response import PageResponse
from app.models.user import User
from app.schemas.user import (
    PasswordUpdateRequest,
    UserAdminUpdateRequest,
    UserCreateRequest,
    UserResponse,
    UserUpdateRequest,
)
from app.utils.password import hash_password, verify_password


def get_user_info(user: User) -> UserResponse:
    """把 ORM 对象转成接口返回的结构"""
    return UserResponse.model_validate(user)


def update_user_info(db: Session, user: User, data: UserUpdateRequest) -> UserResponse:
    """修改当前登录用户的个人信息"""
    # 只取出前端真正传上来的字段，没传的字段保持原值
    payload = data.model_dump(exclude_unset=True, exclude={"role", "status"})

    for field, value in payload.items():
        # name 在数据库里是必填项，传空值时跳过，避免写入 None 导致报错
        if field == "name" and not value:
            continue
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    return UserResponse.model_validate(user)


def update_password(db: Session, user: User, data: PasswordUpdateRequest) -> None:
    """修改当前登录用户的密码"""
    if not verify_password(data.old_password, user.password):
        raise BusinessException(message="原密码错误", code=400)
    if data.old_password == data.new_password:
        raise BusinessException(message="新密码不能和原密码相同", code=400)

    user.password = hash_password(data.new_password)
    db.commit()


def get_user_page(
    db: Session,
    page: int,
    page_size: int,
    keywords: str | None = None,
):
    """管理员分页查询用户，支持按账号或姓名模糊搜索"""
    query = db.query(User)
    if keywords and keywords.strip():
        keyword = keywords.strip()
        query = query.filter(
            or_(
                User.username.ilike(f"%{keyword}%"),
                User.name.ilike(f"%{keyword}%"),
            )
        )

    total = query.count()
    items = (
        query.order_by(User.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return PageResponse(
        list=[UserResponse.model_validate(item) for item in items],
        total=total,
    )


def create_user(db: Session, data: UserCreateRequest) -> UserResponse:
    """管理员新增用户"""
    username = data.username.strip()
    if not username:
        raise BusinessException(message="账号不能为空", code=400)

    exists = db.query(User).filter(User.username == username).first()
    if exists:
        raise BusinessException(message="账号已存在", code=400)

    user = User(
        username=username,
        password=hash_password(data.password),
        name=(data.name or "").strip() or username,
        role=data.role,
        email=data.email,
        phone=data.phone,
        avatar=data.avatar,
        status=str(data.status),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


def update_user(
    db: Session,
    user_id: int,
    data: UserAdminUpdateRequest,
    current_user: User,
) -> UserResponse:
    """管理员编辑用户：账号、姓名、角色、状态和密码都可以修改"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise BusinessException(message="用户不存在", code=404)

    payload = data.model_dump(exclude_unset=True)

    # 防止管理员把自己禁用或降级后失去管理入口
    if payload.get("status") is not None:
        if user.id == current_user.id and payload["status"] != 1:
            raise BusinessException(message="不能禁用当前登录账号", code=400)
    if payload.get("role") is not None:
        if user.id == current_user.id and payload["role"] != "admin":
            raise BusinessException(message="不能取消自己的管理员权限", code=400)

    if payload.get("username"):
        username = payload["username"].strip()
        if not username:
            raise BusinessException(message="账号不能为空", code=400)
        if username != user.username:
            exists = db.query(User).filter(User.username == username).first()
            if exists:
                raise BusinessException(message="账号已存在", code=400)
        user.username = username

    if payload.get("password"):
        user.password = hash_password(payload["password"])

    if "name" in payload:
        name = (payload["name"] or "").strip()
        if not name:
            raise BusinessException(message="姓名不能为空", code=400)
        user.name = name

    if payload.get("role"):
        user.role = payload["role"]

    if "email" in payload:
        user.email = payload["email"]
    if "phone" in payload:
        user.phone = payload["phone"]
    if "avatar" in payload:
        user.avatar = payload["avatar"]
    if payload.get("status") is not None:
        user.status = str(payload["status"])

    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


def delete_user(db: Session, user_id: int, current_user: User) -> None:
    """管理员删除用户，禁止删除当前登录账号"""
    if user_id == current_user.id:
        raise BusinessException(message="不能删除当前登录账号", code=400)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise BusinessException(message="用户不存在", code=404)

    db.delete(user)
    db.commit()
