from sqlalchemy.orm import Session

from app.common.exception import BusinessException
from app.common.response import PageResponse
from app.models.lab import Lab
from app.schemas.lab import (
    LabResponse,
    LabCreateRequest,
    LabUpdateRequest,
)


def get_lab_page(
    db: Session,
    page: int,
    page_size: int,
    keywords: str | None = None,
    status: int | None = None,
):
    """分页查询实验室，支持按实验室名称模糊搜索、按状态过滤"""
    query = db.query(Lab)

    if keywords and keywords.strip():
        keyword = keywords.strip()
        query = query.filter(Lab.name.ilike(f"%{keyword}%"))

    if status is not None:
        query = query.filter(Lab.status == status)

    total = query.count()
    items = (
        query.order_by(Lab.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return PageResponse(
        list=[LabResponse.model_validate(item) for item in items],
        total=total,
    )


def get_lab(db: Session, lab_id: int) -> LabResponse:
    """根据 id 查询单个实验室详情"""
    lab = db.query(Lab).filter(Lab.id == lab_id).first()
    if not lab:
        raise BusinessException(message="实验室不存在", code=404)
    return LabResponse.model_validate(lab)


def create_lab(db: Session, data: LabCreateRequest):
    """新增实验室"""
    exist = db.query(Lab).filter(Lab.name == data.name).first()
    if exist:
        raise BusinessException(message="实验室名称已存在")
    lab = Lab(**data.model_dump())
    db.add(lab)
    db.commit()
    db.refresh(lab)
    return LabResponse.model_validate(lab)


def update_lab(db: Session, lab_id: int, data: LabUpdateRequest):
    """更新实验室"""
    lab = db.query(Lab).filter(Lab.id == lab_id).first()
    if not lab:
        raise BusinessException(message="实验室不存在", code=404)

    # exclude_none=True：自动过滤掉值为 None 的字段，只保留前端传了内容的
    payload = data.model_dump(exclude_none=True)
    for field, value in payload.items():
        setattr(lab, field, value)

    db.commit()
    db.refresh(lab)
    return LabResponse.model_validate(lab)


def delete_lab(db: Session, lab_id: int) -> None:
    """管理员删除实验室"""
    lab = db.query(Lab).filter(Lab.id == lab_id).first()
    if not lab:
        raise BusinessException(message="实验室不存在", code=404)

    db.delete(lab)
    db.commit()
