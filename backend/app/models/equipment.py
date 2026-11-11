from sqlalchemy import ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.database import Base
from app.models.lab import Lab


class Equipment(Base):
    __tablename__ = "equipments"
    __table_args__ = {"comment": "实验室设备表"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="主键ID")
    lab_id: Mapped[int] = mapped_column(ForeignKey("labs.id"), comment="所属实验室ID", nullable=False)
    name: Mapped[str] = mapped_column(String(50), comment="设备名称", nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), comment="说明")
    img: Mapped[str | None] = mapped_column(String(200), comment="图片")
    spec: Mapped[str | None] = mapped_column(String(100), comment="型号规格")
    quantity: Mapped[int] = mapped_column(Integer, comment="数量", default=1)
    status: Mapped[int] = mapped_column(default=1, comment="状态：0-维修，1-正常")
    create_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, comment="创建时间")
    update_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    # 关联实验室，反向可以在Lab里加 equipments: Mapped[list["Equipment"]] = relationship(back_populates="lab")
    lab: Mapped[Lab] = relationship(back_populates="equipments")
