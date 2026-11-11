from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.response import Response
from app.database import get_db
from app.dependencies.auth import get_current_admin, get_current_user
from app.models.user import User
from app.schemas.user import (
    PasswordUpdateRequest,
    UserAdminUpdateRequest,
    UserCreateRequest,
    UserUpdateRequest,
)
from app.services import user_service

router = APIRouter(prefix="/user", tags=["用户信息接口"])


@router.get("/me")
def get_user_info(current_user: User = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return Response.success(data=user_service.get_user_info(current_user))


@router.put("/me")
def update_user_info(
    data: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """修改当前登录用户的个人信息"""
    return Response.success(
        message="修改成功",
        data=user_service.update_user_info(db, current_user, data),
    )


@router.put("/password")
def update_password(
    data: PasswordUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """修改当前登录用户的密码"""
    user_service.update_password(db, current_user, data)
    return Response.success(message="密码修改成功")


@router.get("/list")
def get_user_list(
    page: int = 1,
    page_size: int = 10,
    keywords: str | None = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """管理员分页查询用户"""
    res = user_service.get_user_page(db, page, page_size, keywords)
    return Response.success(data=res)


@router.post("")
def create_user(
    data: UserCreateRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """管理员新增用户"""
    return Response.success(
        message="新增成功",
        data=user_service.create_user(db, data),
    )


@router.put("/{user_id}")
def update_user(
    user_id: int,
    data: UserAdminUpdateRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """管理员编辑用户"""
    return Response.success(
        message="修改成功",
        data=user_service.update_user(db, user_id, data, current_user),
    )


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """管理员删除用户"""
    user_service.delete_user(db, user_id, current_user)
    return Response.success(message="删除成功")
