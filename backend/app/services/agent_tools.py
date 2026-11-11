import datetime
import json

from langchain_core.tools import tool
from sqlalchemy.orm import Session

from app.common.exception import BusinessException
from app.models.user import User
from app.schemas.reservation import ReservationCreateRequest
from app.services import equipment_service, kb_service, lab_service, reservation_service

STATUS_TEXT = {0: "待审核", 1: "已通过", 2: "已拒绝", 3: "已取消"}


def _normalize_date(value: str) -> str:
    """把 2026-9-1 这类写法统一成 2026-09-01，后端按字符串比较日期，格式必须统一"""
    return datetime.datetime.strptime(value.strip(), "%Y-%m-%d").strftime("%Y-%m-%d")


def _normalize_time(value: str) -> str:
    """把 14:00 / 14:00:00 统一成 14:00"""
    value = value.strip()
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.datetime.strptime(value, fmt).strftime("%H:%M")
        except ValueError:
            continue
    raise ValueError(f"时间格式不对：{value}，应该是 HH:MM，例如 14:00")


def build_tools(db: Session, current_user: User):
    """工具工厂：把数据库会话 db 和当前登录用户 current_user 通过闭包塞进每个工具。
    所以 @tool 必须写在 build_tools 内部，不能拎到外面单独定义，否则工具里拿不到 db 和用户。
    """

    @tool
    def search_lab_docs(query: str) -> str:
        """检索实验室的规章制度、安全须知、开放时间、预约流程等文档资料。
        用户问「实验室怎么预约」「有什么安全规定」「几点开放」这类规则性问题时调用，query 传用户的问题原文。
        """
        try:
            result = kb_service.search(query)
            return result or "没有检索到相关的资料"
        except Exception as exc:
            return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)

    @tool
    def list_open_labs(keywords: str = "") -> str:
        """查询当前开放中的实验室列表（含实验室ID、名称、位置、容量、开放时间）。
        用户问有哪些实验室、某个实验室在哪、能坐多少人时调用；keywords 是实验室名称关键字，可为空。
        """
        try:
            keywords = (keywords or "").strip() or None
            page = lab_service.get_lab_page(
                db, page=1, page_size=10, keywords=keywords, status=1
            )
            rows = [
                {
                    "id": item.id,
                    "name": item.name,
                    "location": item.location,
                    "capacity": item.capacity,
                    "open_time": item.open_time,
                    "close_time": item.close_time,
                }
                for item in page.list
            ]
            return json.dumps({"total": page.total, "labs": rows}, ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)

    @tool
    def list_lab_equipments(lab_id: int, keywords: str = "") -> str:
        """查询某个实验室下的设备列表（设备ID、名称、型号、数量、是否可预约）。
        用户问「这个实验室有什么设备」时调用；lab_id 必须从 list_open_labs 的结果里取，不要自己编。
        """
        try:
            keywords = (keywords or "").strip() or None
            page = equipment_service.get_equipment_page(
                db, page=1, page_size=10, lab_id=int(lab_id), keywords=keywords
            )
            rows = [
                {
                    "id": item.id,
                    "name": item.name,
                    "lab_id": item.lab_id,
                    "spec": item.spec,
                    "quantity": item.quantity,
                    "status": "可预约" if item.status == 1 else "维修中",
                }
                for item in page.list
            ]
            return json.dumps(
                {"total": page.total, "equipments": rows}, ensure_ascii=False
            )
        except Exception as exc:
            return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)

    @tool
    def list_my_reservations(status: int | None = None) -> str:
        """查询当前登录用户自己的预约记录（实验室预约和设备预约）。
        用户问「我的预约」「我约了什么时候」「审核通过没有」时调用；status 可不传，
        0=待审核 1=已通过 2=已拒绝 3=已取消。
        """
        try:
            page = reservation_service.get_reservation_page(
                db,
                current_user,
                page=1,
                page_size=10,
                status=status,
                only_mine=True,
                auto_cancel=False,  # 只是查询，不要顺手改数据
            )
            rows = [
                {
                    "id": item.id,
                    "lab_name": item.lab_name,
                    "equipment_name": item.equipment_name or "未预约设备",
                    "type": item.type,
                    "reserve_date": item.reserve_date,
                    "time": f"{item.start_time}-{item.end_time}",
                    "status": STATUS_TEXT.get(item.status, str(item.status)),
                    "remark": item.remark,
                }
                for item in page.list
            ]
            return json.dumps(
                {"total": page.total, "reservations": rows}, ensure_ascii=False
            )
        except Exception as exc:
            return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)

    @tool
    def create_lab_reservation(
        lab_id: int,
        date: str,
        start_time: str,
        end_time: str,
        equipment_id: int | None = None,
        remark: str | None = None,
    ) -> str:
        """真正提交一条预约申请（写入数据库，提交后状态为「待审核」）。
        用户明确说「确认」「确认预约」「就这样预约」之后才调用，没确认前不要调用。
        参数：lab_id 实验室ID（必须来自 list_open_labs）；date 日期，格式 YYYY-MM-DD；
        start_time / end_time 格式 HH:MM，例如 14:00；equipment_id 只在用户要预约具体设备时才传；
        remark 备注可为空。
        """
        try:
            # 1. 先清洗日期、时间的格式，避免写进数据库的字符串没法比较
            reserve_date = _normalize_date(date)
            start = _normalize_time(start_time)
            end = _normalize_time(end_time)

            # 2. 组装成业务层要求的数据对象（注意字段名是 reserve_date，不是 date）
            data = ReservationCreateRequest(
                lab_id=int(lab_id),
                equipment_id=int(equipment_id) if equipment_id else None,
                reserve_date=reserve_date,
                start_time=start,
                end_time=end,
                remark=(remark or "").strip() or None,
            )

            # 3. 交给业务层：校验时间冲突、实验室是否开放、设备归属，最后入库
            reservation = reservation_service.create_reservation(db, current_user, data)

            return json.dumps(
                {
                    "ok": True,
                    "message": "预约已提交，状态为待审核，请等待管理员审核",
                    "reservation_id": getattr(reservation, "id", None),
                    "lab_id": data.lab_id,
                    "equipment_id": data.equipment_id,
                    "date": reserve_date,
                    "start_time": start,
                    "end_time": end,
                },
                ensure_ascii=False,
            )
        except BusinessException as exc:
            # 业务校验失败（时段冲突、实验室关闭、时间不合法等），把原因原样交给大模型
            return json.dumps({"ok": False, "error": exc.message}, ensure_ascii=False)
        except ValueError as exc:
            return json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False)
        except Exception as exc:
            return json.dumps(
                {"ok": False, "error": f"预约失败：{exc}"}, ensure_ascii=False
            )

    @tool
    def get_today() -> str:
        """获取服务器当前的日期，格式示例：2026-09-20。
        用户说「今天」「明天」「后天」「下周」这类相对日期时，必须先调用它拿到今天日期再换算。
        """
        return datetime.datetime.now().strftime("%Y-%m-%d")

    return [
        search_lab_docs,
        list_open_labs,
        list_lab_equipments,
        list_my_reservations,
        create_lab_reservation,
        get_today,
    ]
