"""
自动取消过期预约模块 —— 隔离验收测试
------------------------------------------------
用临时 SQLite 库跑，不碰真实的 MySQL 数据。
运行： backend/venvScripts 里执行 tests/test_expire_scan.py
"""
import os
import sys
import asyncio
import tempfile
import traceback
from datetime import datetime, timedelta

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND_DIR)

DB_FILE = os.path.join(tempfile.gettempdir(), "lab_expire_test.db")
if os.path.exists(DB_FILE):
    os.remove(DB_FILE)
os.environ["DATABASE_URL"] = "sqlite:///" + DB_FILE   # 必须写在 import app.config 之前

from app.database import Base, engine, SessionLocal
from app.models.reservation import Reservation
from app.models.user import User
from app.models.lab import Lab
from app.models.equipment import Equipment
from app.services import reservation_service

PASS, FAIL = [], []


def check(ok, msg):
    (PASS if ok else FAIL).append(msg)
    print(("  [PASS] " if ok else "  [FAIL] ") + msg)


def seed():
    """造 8 条覆盖各种边界的数据"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    before = (now - timedelta(days=2)).strftime("%Y-%m-%d")
    tomorrow = (now + timedelta(days=1)).strftime("%Y-%m-%d")

    cases = [
        ("A 昨天的待审核(已过期)", yesterday, "10:00", 0, 3),
        ("B 今天已结束的待审核",   today,     "00:01", 0, 3),
        ("C 今天还没到时间的待审核", today,   "23:59", 0, 0),
        ("D 明天的待审核",        tomorrow,  "10:00", 0, 0),
        ("E 昨天已通过的(不能动)",  yesterday, "10:00", 1, 1),
        ("F 昨天已拒绝的(不能动)",  yesterday, "10:00", 2, 2),
        ("G 昨天已取消的(不能动)",  yesterday, "10:00", 3, 3),
        ("H 前天的待审核",        before,    "23:59", 0, 3),
    ]
    expect = {}
    for desc, d, end_t, st, exp in cases:
        r = Reservation(user_id=1, lab_id=1, equipment_id=None, reserve_date=d,
                        start_time="08:00", end_time=end_t, remark=desc, status=st)
        db.add(r)
        db.flush()
        expect[r.id] = (desc, exp)
    db.commit()
    db.close()
    return expect


def verify(expect):
    db = SessionLocal()
    for rid, (desc, exp) in expect.items():
        r = db.query(Reservation).filter(Reservation.id == rid).first()
        check(r.status == exp, f"id={rid} {desc}: 期望={exp} 实际={r.status} "
                               f"({r.reserve_date} {r.start_time}-{r.end_time})")
    db.close()


def test_1_logic():
    print("\n===== 1) auto_cancel_expired(db) 判定逻辑 =====")
    expect = seed()
    db = SessionLocal()
    n = reservation_service.auto_cancel_expired(db)
    db.close()
    print(f"  返回取消条数 = {n}（期望 3：A、B、H）")
    check(n == 3, "返回值等于实际取消条数")
    verify(expect)


def test_2_idempotent():
    print("\n===== 2) 重复执行是幂等的（第二次不该再改数据） =====")
    db = SessionLocal()
    n2 = reservation_service.auto_cancel_expired(db)
    db.close()
    print(f"  第二次返回 = {n2}（期望 0）")
    check(n2 == 0, "第二次扫描没有重复改动")


def test_3_background_loop():
    print("\n===== 3) run_expire_scan() 常驻循环 =====")
    reservation_service.SCAN_INTERVAL_SECONDS = 0.2   # 测试时把间隔改小
    expect = seed()

    async def main():
        task = asyncio.create_task(reservation_service.run_expire_scan())
        await asyncio.sleep(0.7)          # 让循环至少跑 2-3 轮
        check(not task.done(), "0.7s 后任务仍在运行（没有崩）")
        if task.done():
            print("    异常：", repr(task.exception()))
        # 模拟 lifespan 关闭
        task.cancel()
        try:
            await task
            check(False, "取消后未抛出 CancelledError")
        except asyncio.CancelledError:
            check(True, "收到 cancel() 后正常结束")

    try:
        asyncio.run(main())
    except Exception:
        print(traceback.format_exc())
        check(False, "run_expire_scan 启动失败")
    verify(expect)


def test_4_survive_db_error():
    print("\n===== 4) 单轮扫描出错不会把任务搞死 =====")
    reservation_service.SCAN_INTERVAL_SECONDS = 0.2
    origin = reservation_service.expire_pending_reservations
    state = {"n": 0}

    def boom():
        state["n"] += 1
        if state["n"] == 1:
            raise RuntimeError("模拟数据库抖动")
        return origin()

    reservation_service.expire_pending_reservations = boom

    async def main():
        task = asyncio.create_task(reservation_service.run_expire_scan())
        await asyncio.sleep(0.7)
        check(not task.done(), "第一轮报错后任务还活着，继续扫第二轮")
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    try:
        asyncio.run(main())
    finally:
        reservation_service.expire_pending_reservations = origin


def test_5_lifespan():
    print("\n===== 5) main.py 的 lifespan 是否真的启动扫描任务 =====")
    reservation_service.SCAN_INTERVAL_SECONDS = 999
    calls = []
    origin = reservation_service.run_expire_scan

    async def fake_scan():
        calls.append(1)
        await asyncio.sleep(999)

    reservation_service.run_expire_scan = fake_scan
    import main
    msgs = [{"type": "lifespan.startup"}, {"type": "lifespan.shutdown"}]
    sent = []

    async def receive():
        return msgs.pop(0)

    async def send(m):
        sent.append(m["type"])
        if m["type"] == "lifespan.startup.complete":
            await asyncio.sleep(0.1)

    try:
        asyncio.run(main.app({"type": "lifespan", "asgi": {"version": "3.0", "spec_version": "2.0"}},
                             receive, send))
        print("  ASGI 消息:", sent)
        check(len(calls) == 1, "FastAPI 启动时创建了扫描任务")
        check(sent == ["lifespan.startup.complete", "lifespan.shutdown.complete"],
              "启动/关闭都正常完成")
    finally:
        reservation_service.run_expire_scan = origin


if __name__ == "__main__":
    print("测试库：", os.environ["DATABASE_URL"])
    print("当前时间：", datetime.now().isoformat(timespec="seconds"))
    test_1_logic()
    test_2_idempotent()
    test_3_background_loop()
    test_4_survive_db_error()
    test_5_lifespan()
    print(f"\n===== 汇总：通过 {len(PASS)}，失败 {len(FAIL)} =====")
    for f in FAIL:
        print("  失败项：", f)
    sys.exit(1 if FAIL else 0)
