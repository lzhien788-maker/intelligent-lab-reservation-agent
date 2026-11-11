from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.response import Response
from app.database import get_db
from app.dependencies.auth import get_current_admin, get_current_user
from app.models.user import User
from app.schemas.reservation import ReservationCreateRequest, ReservationStatusRequest
from app.services import reservation_service

router = APIRouter(prefix="/reservation", tags=["预约相关接口"])

# 状态约定：0 待审核 / 1 已通过 / 2 已拒绝 / 3 已取消


@router.post("")
def create_reservation(
    data: ReservationCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """提交预约，登录即可调用"""
    res = reservation_service.create_reservation(db, current_user, data)
    return Response.success(message="预约提交成功，等待管理员审核", data=res)


@router.get("/list")
def get_reservation_list(
    page: int = 1,
    page_size: int = 10,
    status: int | None = None,
    only_mine: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """分页列表：学生只看自己，管理员看全部（only_mine=true 时管理员也只看自己）"""
    res = reservation_service.get_reservation_page(
        db, current_user, page, page_size, status, only_mine
    )
    return Response.success(data=res)


@router.put("/{reservation_id}/audit")
def audit_reservation(
    reservation_id: int,
    data: ReservationStatusRequest,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """审核预约（仅管理员）：status 1 通过 / 2 拒绝"""
    res = reservation_service.audit_reservation(db, reservation_id, data.status)
    return Response.success(message="审核完成", data=res)


@router.put("/{reservation_id}/cancel")
def cancel_reservation(
    reservation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """取消预约：本人可取消自己的（待审核/已通过），管理员可取消任意一条"""
    reservation_service.cancel_reservation(db, reservation_id, current_user)
    return Response.success(message="已取消预约")
