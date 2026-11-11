# 智能实验室预约系统

一个前后端分离的实验室预约管理系统，内置基于 **大语言模型（LLM）+ RAG 检索增强生成** 的 AI 智能助手，支持学生在线浏览实验室、提交预约，管理员审核管理，以及通过自然语言对话完成实验室查询、设备查询和预约下单。

> 后端采用 FastAPI + LangGraph 构建 AI Agent，前端采用 Vue 3 + Element Plus，数据库使用 MySQL，知识库使用 ChromaDB 向量库。

## 功能特性

- **用户认证**：注册 / 登录，基于 JWT + bcrypt 密码加密，Token 失效自动跳转登录。
- **角色权限**：区分「学生」与「管理员」两种角色，前端路由守卫 + 后端依赖注入双重鉴权。
- **实验室管理**：管理员对实验室进行增删改查；学生浏览开放中的实验室及详情。
- **设备管理**：设备归属于具体实验室，管理员维护设备信息与可用状态。
- **预约管理**：
  - 学生提交实验室 / 设备预约，后端校验日期、时间、开放时段与时段冲突；
  - 管理员审核（通过 / 拒绝），用户可取消自己的预约；
  - 后台定时任务自动取消「已过期但未审核」的预约。
- **AI 智能助手**：
  - 基于 LangGraph 编排的 Agent，可调用真实业务工具；
  - 支持 SSE 流式输出，前端逐字渲染；
  - 基于 ChromaDB + 中文向量模型的 RAG 知识库问答。
- **文件上传**：支持图片 / 文档上传（类型与大小校验），静态文件挂载访问。
- **统一响应与异常处理**：全局统一返回格式与异常兜底。

## 技术栈

### 后端

| 分类 | 技术 |
| --- | --- |
| 语言 | Python 3.11+ |
| Web 框架 | FastAPI 0.115 |
| ORM | SQLAlchemy 2.0 |
| 数据库 | MySQL（PyMySQL 驱动） |
| 数据校验 | Pydantic v2 / pydantic-settings |
| 认证 | PyJWT + bcrypt |
| AI Agent | LangChain + LangGraph |
| 大模型 | 兼容 OpenAI 协议的大模型（默认配置 DeepSeek） |
| 向量数据库 | ChromaDB |
| 向量模型 | sentence-transformers（BAAI/bge-small-zh-v1.5） |
| 服务器 | Uvicorn |

### 前端

| 分类 | 技术 |
| --- | --- |
| 框架 | Vue 3.5 |
| 构建工具 | Vite 8 |
| UI 组件库 | Element Plus |
| 路由 | Vue Router |
| HTTP 请求 | Axios（流式接口使用原生 fetch） |
| 运行环境 | Node.js 22.18+ / 24.12+ |

## 项目结构

```
.
├── backend/                     # FastAPI 后端
│   ├── app/
│   │   ├── api/                 # 路由层（接口定义）
│   │   ├── common/              # 统一响应、异常处理
│   │   ├── dependencies/        # 依赖注入（JWT 鉴权）
│   │   ├── models/              # SQLAlchemy 数据模型
│   │   ├── schemas/             # Pydantic 请求/响应模型
│   │   ├── services/            # 业务逻辑层（含 AI Agent）
│   │   ├── utils/               # 工具（JWT、密码加密）
│   │   ├── config.py            # 配置管理
│   │   └── database.py          # 数据库连接与会话
│   ├── data/
│   │   ├── kb/                  # 知识库 Markdown 文档
│   │   └── chroma/              # ChromaDB 向量库持久化（运行时生成，不提交）
│   ├── scripts/
│   │   └── export_db.py         # 数据库导出脚本（生成 sql/lab_agent.sql）
│   ├── sql/
│   │   └── lab_agent.sql        # 数据库初始化脚本（结构 + 初始数据）
│   ├── tests/                   # 测试脚本
│   ├── uploads/                 # 上传文件目录
│   ├── .env.example             # 环境变量模板
│   ├── main.py                  # 应用入口
│   └── requirements.txt         # Python 依赖
└── frontend/                    # Vue 3 前端
    ├── src/
    │   ├── api/                 # 接口封装
    │   ├── assets/              # 静态资源
    │   ├── layout/              # 布局组件
    │   ├── router/              # 路由与守卫
    │   ├── utils/               # 工具（axios 封装、token 存储）
    │   └── view/                # 页面组件
    ├── package.json
    └── vite.config.js
```

## AI 智能助手架构

智能助手是系统的核心亮点，采用 **Agent + 工具调用 + RAG** 的组合方案：

1. **Agent 编排**：使用 LangGraph 构建 `agent`（大模型）与 `tools`（工具执行）两个节点的状态图，大模型按需决定是否调用工具。
2. **业务工具**：Agent 可调用以下真实工具，直接读写数据库：
   - `search_lab_docs`：检索实验室规章制度、安全须知、开放时间等知识库文档；
   - `list_open_labs`：查询开放中的实验室；
   - `list_lab_equipments`：查询实验室下的设备；
   - `list_my_reservations`：查询当前用户的预约记录；
   - `create_lab_reservation`：提交预约（写入数据库）；
   - `get_today`：获取服务器当前日期（用于换算「今天 / 明天 / 下周」等相对日期）。
3. **RAG 知识库**：将 `backend/data/kb/` 下的 Markdown 文档用中文向量模型（`bge-small-zh-v1.5`）向量化存入 ChromaDB，检索出的相关内容作为上下文注入提示词，避免大模型编造信息。
4. **流式输出**：后端通过 SSE（Server-Sent Events）边生成边推送，前端使用原生 `fetch` 逐字渲染，并在界面实时展示工具调用过程。

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 22.18+ / 24.12+
- MySQL 8.0+

### 0. 初始化数据库

项目已经把数据库结构和初始数据（8 个实验室、29 台设备、3 个测试账号）导出成 SQL 脚本，直接导入即可，不用自己建表：

**方式一：Navicat / DBeaver等图形化工具**

1. 新建数据库 `lab_agent`（字符集 `utf8mb4`）；
2. 右键该库 →「运行 SQL 文件」→ 选择 `backend/sql/lab_agent.sql`；
3. 执行完成后刷新，能看到 `users`、`labs`、`equipments`、`reservations` 四张表。

**方式二：命令行**

```bash
mysql -u root -p < backend/sql/lab_agent.sql
```

脚本内容说明：

| 表 | 是否含数据 | 说明 |
| --- | --- | --- |
| `users` | 含 | 初始账号，管理员 + 两个学生账号 |
| `labs` | 含 | 8 个实验室及其开放时间、配图 |
| `equipments` | 含 | 各实验室下的设备清单 |
| `reservations` | 仅结构 | 预约记录属于个人数据，不预置，登录后自己产生 |

> 如果之后你又往数据库里加了数据，想重新生成这份脚本，执行：
> ```bash
> cd backend
> .\.venv\Scripts\python.exe scripts\export_db.py
> ```

### 1. 启动后端

```bash
cd backend

# 创建并激活虚拟环境（Windows PowerShell）
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 安装依赖
pip install -r requirements.txt

# 复制环境变量模板，再改成自己的配置
Copy-Item .env.example .env
```

在 `backend/.env` 中配置环境变量（参考下方「环境变量配置」），然后启动服务：

```bash
uvicorn main:app --reload --port 8000
```

后端默认运行在 `http://127.0.0.1:8000`，接口文档可在 `/docs` 查看（FastAPI 自动生成）。

### 2. 启动前端

```bash
cd frontend

npm install
npm run dev
```

前端开发服务器默认运行在 `http://localhost:5173`，已配置代理将 `/api` 与 `/uploads` 转发至后端 `http://127.0.0.1:8000`。

## 演示账号

导入 `backend/sql/lab_agent.sql` 后，系统内已预置以下账号，可直接登录体验：

| 账号 | 密码 | 角色 | 可体验的功能 |
| --- | --- | --- | --- |
| `admin` | `12345678` | 管理员 | 实验室 / 设备 / 用户管理、预约审核、AI 智能助手 |
| `aaa` | `111111` | 学生 | 浏览实验室、提交预约、我的预约、AI 智能助手 |
| `111` | `1234567` | 学生 | 同上（备用测试账号） |

> 以上账号仅用于本地演示与教学，**请勿用于任何真实环境**。
> 你也可以直接点击登录页的「立即注册」创建自己的账号（新注册账号默认为学生角色）。

## 环境变量配置

仓库里只提交了模板 `backend/.env.example`，真实配置请复制一份改成自己的值：

```bash
cd backend
Copy-Item .env.example .env
```

后端 `backend/.env`：

| 变量 | 说明 | 示例 |
| --- | --- | --- |
| `DATABASE_URL` | MySQL 连接串 | `mysql+pymysql://root:root@127.0.0.1:3306/lab_agent` |
| `JWT_SECRET_KEY` | JWT 签名密钥 | 随机字符串 |
| `JWT_EXPIRE_HOURS` | Token 有效期（小时） | `24` |
| `JWT_ALGORITHM` | JWT 加密算法 | `HS256` |
| `LLM_API_KEY` | 大模型 API Key | `sk-xxx` |
| `LLM_MODEL` | 大模型名称 | `deepseek-v4-flash` |
| `LLM_BASE_URL` | 大模型接口地址 | `https://api.deepseek.com` |

前端 `frontend/.env.development`：

| 变量 | 说明 | 示例 |
| --- | --- | --- |
| `VITE_API_BASE_URL` | 接口基础地址 | 留空则走 Vite 代理 |

> 注意：`.env` 包含敏感信息，请勿提交到公开仓库，建议将其加入 `.gitignore`。

## API 接口概览

所有接口统一前缀 `/api`，返回格式统一为 `{ code, message, data }`。

| 模块 | 方法 | 路径 | 说明 | 权限 |
| --- | --- | --- | --- | --- |
| 认证 | POST | `/auth/register` | 注册 | 公开 |
| 认证 | POST | `/auth/login` | 登录 | 公开 |
| 用户 | GET | `/user/me` | 当前用户信息 | 登录 |
| 用户 | PUT | `/user/me` | 修改个人信息 | 登录 |
| 用户 | PUT | `/user/password` | 修改密码 | 登录 |
| 用户 | GET/POST/PUT/DELETE | `/user` | 用户管理 | 管理员 |
| 实验室 | GET | `/lab/list` | 分页查询实验室 | 登录 |
| 实验室 | GET | `/lab/{id}` | 实验室详情 | 登录 |
| 实验室 | POST/PUT/DELETE | `/lab` | 实验室管理 | 管理员 |
| 设备 | GET | `/equipment/list` | 分页查询设备 | 登录 |
| 设备 | POST/PUT/DELETE | `/equipment` | 设备管理 | 管理员 |
| 预约 | POST | `/reservation` | 提交预约 | 登录 |
| 预约 | GET | `/reservation/list` | 分页查询预约 | 登录 |
| 预约 | PUT | `/reservation/{id}/audit` | 审核预约 | 管理员 |
| 预约 | PUT | `/reservation/{id}/cancel` | 取消预约 | 登录 |
| AI | POST | `/ai/chat` | AI 对话（非流式） | 登录 |
| AI | POST | `/ai/chat/stream` | AI 对话（SSE 流式） | 登录 |
| 文件 | POST | `/files/upload` | 文件上传 | 登录 |

预约状态约定：`0` 待审核 / `1` 已通过 / `2` 已拒绝 / `3` 已取消。

## 测试

后端提供两个独立测试脚本（不依赖 pytest）：

```bash
cd backend

# 自动取消过期预约模块测试（使用临时 SQLite，不污染真实数据）
.\.venv\Scripts\python.exe tests/test_expire_scan.py

# AI 对话接口连通性测试（需后端已启动，会真实调用一次大模型）
.\.venv\Scripts\python.exe tests/test_ai_chat.py
```
