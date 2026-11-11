from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.response import Response
from app.database import get_db
from app.dependencies.auth import get_current_admin, get_current_user
from app.models.user import User
from app.schemas.equipment import (
    EquipmentCreateRequest,
    EquipmentUpdateRequest,
)
from app.services import equipment_service

router = APIRouter(prefix="/equipment", tags=["设备信息接口"])


@router.get("/list")
def get_equipment_list(
    page: int = 1,
    page_size: int = 10,
    keywords: str | None = None,
    lab_id: int | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """分页查询设备，登录即可访问；传 lab_id 只查某个实验室的设备"""
    res = equipment_service.get_equipment_page(db, page, page_size, keywords, lab_id)
    return Response.success(data=res)


@router.post("")
def create_equipment(
    data: EquipmentCreateRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """管理员创建设备"""
    return Response.success(
        message="新增成功",
        data=equipment_service.create_equipment(db, data),
    )


@router.put("/{eq_id}")
def update_equipment(
    eq_id: int,
    data: EquipmentUpdateRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """管理员编辑设备"""
    return Response.success(
        message="修改成功",
        data=equipment_service.update_equipment(db, eq_id, data),
    )


@router.delete("/{eq_id}")
def delete_equipment(
    eq_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """管理员删除设备"""
    equipment_service.delete_equipment(db, eq_id)
    return Response.success(message="删除成功")
