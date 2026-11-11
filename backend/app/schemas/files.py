from pydantic import BaseModel


class FileResponse(BaseModel):
    """文件上传成功后返回的数据"""

    original_name: str
    disk_name: str
    # 文件大小，单位字节；file.size 本身是 int，个别情况下可能为 None
    size: int | None = None
    url: str


