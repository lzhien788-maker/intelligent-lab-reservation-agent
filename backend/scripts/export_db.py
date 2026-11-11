r"""
把 MySQL 数据库导出成可以直接导入的 .sql 文件（结构 + 数据）。

为什么不用 mysqldump？
    这个项目里没有把 MySQL 的 bin 目录加到 PATH，直接调用 mysqldump 会“命令不存在”。
    用 Python + pymysql 自己拼 SQL，只依赖 requirements.txt 里已有的 pymysql，换台电脑也能用。

用法（在 backend 目录下执行）：
    .\.venv\Scripts\python.exe scripts\export_db.py

默认读取 .env 里的 DATABASE_URL，输出到 sql/lab_agent.sql。
"""
import os
import sys
from datetime import date, datetime, time
from decimal import Decimal
from pathlib import Path

import pymysql

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

# 这些表只导结构、不导数据（个人测试产生的记录，不适合当初始数据）
DATA_SKIP_TABLES = {"reservations"}

# 建表顺序：被引用的表必须排在前面，否则新库导入时外键找不到目标表
TABLE_ORDER = ["users", "labs", "equipments", "reservations"]


def parse_database_url(url: str) -> dict:
    """mysql+pymysql://root:root@127.0.0.1:3306/lab_agent -> pymysql 连接参数"""
    without_scheme = url.split("://", 1)[1]
    credentials, rest = without_scheme.split("@", 1)
    user, password = credentials.split(":", 1)
    host_port, database = rest.split("/", 1)
    host, port = host_port.split(":", 1) if ":" in host_port else (host_port, 3306)
    return {
        "host": host,
        "port": int(port),
        "user": user,
        "password": password,
        "database": database.split("?")[0],
    }


def to_sql_value(value) -> str:
    """把 Python 值转成 SQL 字面量"""
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime, date, time)):
        return "'" + value.isoformat() + "'"
    if isinstance(value, bytes):
        return "0x" + value.hex()
    text = str(value).replace("\\", "\\\\").replace("'", "\\'")
    return "'" + text + "'"


def main() -> None:
    # 直接读 .env，避免 import app.config 时触发一堆初始化
    env_path = BACKEND_DIR / ".env"
    database_url = None
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("DATABASE_URL="):
            database_url = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not database_url:
        raise SystemExit("没有在 backend/.env 里找到 DATABASE_URL")

    params = parse_database_url(database_url)
    output_path = BACKEND_DIR / "sql" / "lab_agent.sql"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    conn = pymysql.connect(charset="utf8mb4", **params)
    cur = conn.cursor()

    cur.execute("SHOW TABLES")
    tables = [row[0] for row in cur.fetchall()]
    # 按依赖顺序排序（不在列表里的表排在最后）
    tables.sort(key=lambda t: (TABLE_ORDER.index(t) if t in TABLE_ORDER else len(TABLE_ORDER)))

    lines = []
    lines.append("-- 智能实验室预约系统 数据库初始化脚本")
    lines.append("-- 由 backend/scripts/export_db.py 自动生成")
    lines.append("-- 导入方式：mysql -u root -p < lab_agent.sql  或 Navicat 里“运行 SQL 文件”")
    lines.append("")
    lines.append("SET NAMES utf8mb4;")
    lines.append("SET FOREIGN_KEY_CHECKS = 0;")
    lines.append("")
    lines.append(f"CREATE DATABASE IF NOT EXISTS `{params['database']}` "
                 "DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;")
    lines.append(f"USE `{params['database']}`;")
    lines.append("")

    for table in tables:
        cur.execute(f"SHOW CREATE TABLE `{table}`")
        create_sql = cur.fetchone()[1]
        lines.append(f"-- ---------------- {table} ----------------")
        lines.append(f"DROP TABLE IF EXISTS `{table}`;")
        lines.append(create_sql + ";")
        lines.append("")

        if table in DATA_SKIP_TABLES:
            lines.append(f"-- {table}：只建表，不插入数据")
            lines.append("")
            continue

        cur.execute(f"SELECT * FROM `{table}`")
        columns = [d[0] for d in cur.description]
        rows = cur.fetchall()
        if not rows:
            continue

        column_list = ", ".join(f"`{c}`" for c in columns)
        for row in rows:
            values = ", ".join(to_sql_value(v) for v in row)
            lines.append(f"INSERT INTO `{table}` ({column_list}) VALUES ({values});")
        lines.append("")

    lines.append("SET FOREIGN_KEY_CHECKS = 1;")
    lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    conn.close()

    size_kb = output_path.stat().st_size / 1024
    print(f"已导出 {len(tables)} 张表 -> {output_path}  ({size_kb:.1f} KB)")
    for table in tables:
        cur_note = "仅结构" if table in DATA_SKIP_TABLES else "含数据"
        print(f"  - {table} ({cur_note})")


if __name__ == "__main__":
    main()
