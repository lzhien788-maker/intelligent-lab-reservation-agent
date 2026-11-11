from pydantic import BaseModel, ConfigDict


class ReservationCreateRequest(BaseModel):
    lab_id: int
    # 空表示只预约实验室，不预约具体设备
    equipment_id: int | None = None
    reserve_date: str
    start_time: str
    end_time: str
    remark: str | None = None


class ReservationStatusRequest(BaseModel):
    # 1-已通过 2-已拒绝
    status: int


class ReservationResponse(BaseModel):
    id: int
    user_id: int
    user_name: str | None = None
    lab_id: int
    lab_name: str | None = None
    equipment_id: int | None = None
    equipment_name: str | None = None
    # 预约类型：实验室预约 / 设备预约
    type: str | None = None
    reserve_date: str
    start_time: str
    end_time: str
    remark: str | None = None
    status: int

    model_config = ConfigDict(from_attributes=True)
