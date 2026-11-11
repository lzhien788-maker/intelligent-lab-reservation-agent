from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_EXPIRE_HOURS: int = 24
    JWT_ALGORITHM: str = "HS256"
    LLM_API_KEY: str
    LLM_MODEL: str
    LLM_BASE_URL: str
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env", env_file_encoding="utf-8"

    )

settings = Settings()

# 上传文件保存目录（BASE_DIR 上面已定义为 backend 根目录，不要再重新赋值）
UPLOAD_DIR = BASE_DIR / "uploads"
# 创建上传文件夹，parents=True 自动创建父目录，exist_ok=True 文件夹存在也不报错
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 最大文件大小 100MB
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100M

# 允许上传的后缀集合
ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".webp",
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".zip",
}







