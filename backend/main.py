import traceback

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from app.config import UPLOAD_DIR
from app.models.user import User
from app.models.lab import Lab
from app.models.equipment import Equipment
from app.models.reservation import Reservation
from contextlib import asynccontextmanager
import asyncio
from app.database import Base, engine
from app.api import api
from app.common.exception import (
BusinessException,
business_exception_handler,
http_exception_handler,
validation_exception_handler,
global_exception_handler
)
from starlette.middleware.cors import CORSMiddleware

from app.services import reservation_service, kb_service

# 自动帮我们创建数据库和数据库表
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await asyncio.to_thread(kb_service.warmup())
    except Exception:
        traceback.print_exc()

    # 【项目启动时】创建后台异步任务：定时扫描过期预约
    task = asyncio.create_task(reservation_service.run_expire_scan())
    yield   # 这里卡住，FastAPI正式接收请求、运行
    # 【项目关闭时】取消后台任务
    task.cancel()
    try:
        await task  # 等待任务真正结束，捕获取消异常
    except asyncio.CancelledError:
        print("过期扫描任务已经正常取消")

app = FastAPI(lifespan=lifespan)
app.include_router(api)

app.add_exception_handler(BusinessException, business_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)


origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 上传目录由 app/config.py 统一管理（目录已自动创建）

# 挂载静态的文件目录  http://127.0.0.1:8000/uploads/xxx.jpg
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

@app.get("/")
def root():
    return {"message": "FastAPI工程正在运行中"}

