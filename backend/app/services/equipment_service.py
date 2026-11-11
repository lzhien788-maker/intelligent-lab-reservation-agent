from sqlalchemy.orm import Session

from app.common.exception import BusinessException
from app.common.response import PageResponse
from app.models.equipment import Equipment
from app.models.lab import Lab
from app.schemas.equipment import (
    EquipmentResponse,
    EquipmentCreateRequest,
    EquipmentUpdateRequest,
)


def get_equipment_page(
    db: Session,
    page: int,
    page_size: int,
    keywords: str | None = None,
    lab_id: int | None = None,
):
    """分页查询设备，支持按设备名称模糊搜索、按所属实验室过滤，带出实验室名称"""
    query = db.query(Equipment, Lab.name.label("lab_name")).join(
        Lab, Equipment.lab_id == Lab.id
    )

    if keywords and keywords.strip():
        keyword = keywords.strip()
        query = query.filter(Equipment.name.ilike(f"%{keyword}%"))

    if lab_id is not None:
        query = query.filter(Equipment.lab_id == lab_id)

    total = query.count()
    rows = (
        query.order_by(Equipment.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    resp_list = []
    for eq, lab_name in rows:
        eq_resp = EquipmentResponse.model_validate(eq)
        eq_resp.lab_name = lab_name
        resp_list.append(eq_resp)

    return PageResponse(
        list=resp_list,
        total=total,
    )


def create_equipment(db: Session, data: EquipmentCreateRequest):
    """创建设备"""
    lab = db.query(Lab).filter(Lab.id == data.lab_id).first()
    if not lab:
        raise BusinessException(message="所选实验室不存在")

    equipment = Equipment(**data.model_dump())
    db.add(equipment)
    db.commit()
    db.refresh(equipment)

    eq_with_lab = (
        db.query(Equipment, Lab.name.label("lab_name"))
        .join(Lab, Equipment.lab_id == Lab.id)
        .filter(Equipment.id == equipment.id)
        .first()
    )
    eq_resp = EquipmentResponse.model_validate(eq_with_lab[0])
    eq_resp.lab_name = eq_with_lab[1]
    return eq_resp


def update_equipment(db: Session, equipment_id: int, data: EquipmentUpdateRequest):
    """更新设备"""
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not equipment:
        raise BusinessException(message="设备不存在", code=404)

    payload = data.model_dump(exclude_none=True)
    lab_id = payload.get("lab_id", equipment.lab_id)
    name = payload.get("name", equipment.name)

    lab = db.query(Lab).filter(Lab.id == lab_id).first()
    if not lab:
        raise BusinessException(message="实验室不存在")

    # 同一个实验室下，排除自身，检查是否已有同名设备
    exist = (
        db.query(Equipment)
        .filter(
            Equipment.lab_id == lab_id,
            Equipment.name == name,
            Equipment.id != equipment_id,
        )
        .first()
    )
    if exist:
        raise BusinessException(message="该实验室下已存在同名设备")

    for field, value in payload.items():
        setattr(equipment, field, value)

    db.commit()
    db.refresh(equipment)

    eq_with_lab = (
        db.query(Equipment, Lab.name.label("lab_name"))
        .join(Lab, Equipment.lab_id == Lab.id)
        .filter(Equipment.id == equipment.id)
        .first()
    )
    eq_resp = EquipmentResponse.model_validate(eq_with_lab[0])
    eq_resp.lab_name = eq_with_lab[1]
    return eq_resp


def delete_equipment(db: Session, eq_id: int) -> None:
    """删除设备"""
    equipment = db.query(Equipment).filter(Equipment.id == eq_id).first()
    if not equipment:
        raise BusinessException(message="设备不存在", code=404)

    db.delete(equipment)
    db.commit()
