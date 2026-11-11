from datetime import datetime
import asyncio
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session
from app.common.exception import BusinessException
from app.common.response import PageResponse
from app.database import SessionLocal
from app.models.equipment import Equipment
from app.models.lab import Lab
from app.models.reservation import Reservation
from app.models.user import User
from app.schemas.reservation import (
    ReservationCreateRequest,
    ReservationResponse,
)

# 后台扫描过期预约的间隔（秒）；测试时可以临时改成 1
SCAN_INTERVAL_SECONDS = 60


def _build_query(db: Session):
    """预约 + 实验室名 + 设备名 + 预约人名，一次查出来，不用循环里再查库"""
    return (
        db.query(
            Reservation,
            Lab.name.label("lab_name"),
            Equipment.name.label("equipment_name"),
            User.username.label("user_name"),
        )
        .join(Lab, Reservation.lab_id == Lab.id)
        .outerjoin(Equipment, Reservation.equipment_id == Equipment.id)
        .join(User, Reservation.user_id == User.id)
    )


def _to_response(row) -> ReservationResponse:
    reservation, lab_name, equipment_name, user_name = row
    # 显式赋值，模型里没有的字段（type）单独补，避免 from_attributes 拿不到属性报错
    return ReservationResponse(
        id=reservation.id,
        user_id=reservation.user_id,
        user_name=user_name,
        lab_id=reservation.lab_id,
        lab_name=lab_name,
        equipment_id=reservation.equipment_id,
        equipment_name=equipment_name,
        type="设备预约" if reservation.equipment_id else "实验室预约",
        reserve_date=reservation.reserve_date,
        start_time=reservation.start_time,
        end_time=reservation.end_time,
        remark=reservation.remark,
        status=reservation.status,
    )


def auto_cancel_expired(db: Session) -> int:
    """自动取消「已经过期但还没审核」的预约（status=0 -> 3）

    「过期」= 预约日期早于今天，或者日期是今天但结束时间已经过了
    （字符串是 "YYYY-MM-DD" / "HH:MM" 定长格式，直接比大小就是比时间先后）
    """
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    cur_time = now.strftime("%H:%M")
    expired = (
        db.query(Reservation)
        .filter(
            Reservation.status == 0,
            or_(
                Reservation.reserve_date < today,                                        # 以前的日期
                and_(Reservation.reserve_date == today, Reservation.end_time <= cur_time),  # 今天但已结束
            ),
        )
        .all()
    )
    if not expired:
        return 0
    for item in expired:
        item.status = 3
    db.commit()
    return len(expired)



def create_reservation(db: Session, current_user: User, data: ReservationCreateRequest):
    """学生提交预约：先做各种合法性校验，再查时段冲突，最后入库"""
    now = datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M")

    # 1. 不能预约过去的日期
    if data.reserve_date < current_date:
        raise BusinessException(message="预约日期不能小于当前的日期")

    # 2. 结束时间不能早于开始时间
    if data.end_time < data.start_time:
        raise BusinessException(message="预约的结束时间不能小于开始时间")

    # 3. 如果今天预约，开始时间不能已经过去了
    if data.reserve_date == current_date and data.start_time < current_time:
        raise BusinessException(message="预约开始时间不能小于当前的时间")

    # 4. 实验室是否存在
    lab = db.query(Lab).filter(Lab.id == data.lab_id).first()
    if not lab:
        raise BusinessException(message="实验室不存在")

    # 5. 实验室是否开放
    if lab.status != 1:
        raise BusinessException(message="实验室已关闭")

    # 6. 必须在实验室开放时间内
    if lab.open_time and data.start_time < lab.open_time:
        raise BusinessException(message="预约开始时间不能早于实验室开放时间")
    if lab.close_time and data.end_time > lab.close_time:
        raise BusinessException(message="预约结束时间不能晚于实验室关闭时间")

    # 7. 设备校验（只有传了设备才校验）
    if data.equipment_id:
        equipment = db.query(Equipment).filter(Equipment.id == data.equipment_id).first()
        if not equipment:
            raise BusinessException(message="预约的设备不存在")
        # 设备必须是这个实验室里的，防止跨实验室乱约
        if equipment.lab_id != data.lab_id:
            raise BusinessException(message="该设备不属于所选实验室")
        if equipment.status != 1:
            raise BusinessException(message="该设备正在维修，暂不可预约")

    # 8. 时段冲突：同一实验室（或同一设备）、同一天、状态为待审核/已通过、时间段重叠
    query = db.query(Reservation).filter(
        Reservation.lab_id == data.lab_id,
        Reservation.reserve_date == data.reserve_date,
        Reservation.status.in_([0, 1]),
        Reservation.start_time < data.end_time,
        Reservation.end_time > data.start_time,
    )
    if data.equipment_id:
        query = query.filter(Reservation.equipment_id == data.equipment_id)
    else:
        query = query.filter(Reservation.equipment_id.is_(None))

    if query.first():
        raise BusinessException(message="该时段已预约，不可重复预约")

    # 9. 全部校验通过，创建预约（user_id 取当前登录用户，不信任前端传的）
    reservation = Reservation(
        user_id=current_user.id,
        lab_id=data.lab_id,
        equipment_id=data.equipment_id,
        reserve_date=data.reserve_date,
        start_time=data.start_time,
        end_time=data.end_time,
        remark=data.remark,
        status=0,
    )
    db.add(reservation)
    db.commit()
    db.refresh(reservation)

    row = _build_query(db).filter(Reservation.id == reservation.id).first()
    return _to_response(row)


def get_reservation_page(
    db: Session,
    current_user: User,
    page: int,
    page_size: int,
    status: int | None = None,
    only_mine: bool = False,
    auto_cancel: bool = True,
):
    """预约列表：
    - 学生：永远只看自己的
    - 管理员：默认看全部；only_mine=True 时只看自己的（「我的预约」页面用）
    auto_cancel=True 时每次查询前先过一次自动取消，保证过期待审核不会一直挂着；
    AI 工具这类「只查询」的场景传 False，避免查一次就顺手改了数据
    """
    if auto_cancel:
        auto_cancel_expired(db)

    query = _build_query(db)

    if only_mine or current_user.role != "admin":
        query = query.filter(Reservation.user_id == current_user.id)

    if status is not None:
        query = query.filter(Reservation.status == status)

    total = query.count()
    rows = (
        query.order_by(Reservation.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return PageResponse(list=[_to_response(row) for row in rows], total=total)


def audit_reservation(db: Session, reservation_id: int, status: int):
    """管理员审核预约：只有待审核(0)的才能改成 已通过(1) / 已拒绝(2)"""
    if status not in (1, 2):
        raise BusinessException(message="审核状态只能是 1（通过）或 2（拒绝）")

    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        raise BusinessException(message="预约不存在", code=404)
    if reservation.status != 0:
        raise BusinessException(message="该预约已审核过，不能重复审核")

    reservation.status = status
    db.commit()
    db.refresh(reservation)

    row = _build_query(db).filter(Reservation.id == reservation.id).first()
    return _to_response(row)


# 兼容旧名字（之前调用叫 update_reservation_status）
update_reservation_status = audit_reservation


def cancel_reservation(db: Session, reservation_id: int, current_user: User):
    """取消预约：只能取消自己的，且待审核/已通过的才能取消"""
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        raise BusinessException(message="预约不存在", code=404)

    if current_user.role != "admin" and reservation.user_id != current_user.id:
        raise BusinessException(message="只能取消自己的预约", code=403)

    if reservation.status == 3:
        raise BusinessException(message="该预约已取消")
    if reservation.status == 2:
        raise BusinessException(message="该预约已被拒绝，无需取消")

    reservation.status = 3
    db.commit()
    return None

def expire_pending_reservations() -> int:
    """后台任务用：自己开一个会话，扫一次，返回取消了多少条"""
    db = SessionLocal()
    try:
        return auto_cancel_expired(db)
    finally:
        db.close()


async def run_expire_scan():
    """后台常驻任务：每隔 SCAN_INTERVAL_SECONDS 秒扫一次过期预约"""
    while True:
        try:
            count = expire_pending_reservations()
            if count:
                print(f"[过期扫描] 已自动取消 {count} 条过期未审核的预约")
        except Exception as e:
            # 单次扫描失败（网络/数据库抖动）不能让整个任务死掉，打印后继续下一轮
            print(f"[过期扫描] 本轮扫描失败：{type(e).__name__}: {e}")
        await asyncio.sleep(SCAN_INTERVAL_SECONDS)









