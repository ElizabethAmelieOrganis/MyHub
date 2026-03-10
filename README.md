# MyHub - 简易的命令行社交与文件系统

MyHub 是一个基于 Client-Server 架构的轻量级命令行应用程序。它集成了用户认证、即时消息留言板以及文件上传与评论功能，旨在提供一个简单、纯粹的交互环境。

## ✨ 主要功能

- **用户系统**: 支持用户登录。
- **消息留言板 (`msg`)**:
  - 发布全站公开留言。
  - 浏览留言列表（支持分页限制 `-n` 或查看全部 `--all`）。
  - 针对特定留言进行回复。
- **文件系统 (`files`)**:
  - 上传本地文件到服务器（支持自定义存储文件名）。
  - 浏览已上传的文件列表。
  - 查看文件详情 (`look -id`)，包括文件大小、上传时间等。
  - **文件专属留言区**: 在查看文件详情时，可以针对该文件发布和查看专属评论。

## 🛠 技术栈

- **服务端 (Server)**:
  - [FastAPI](https://fastapi.tiangolo.com/): 高性能的 Web 框架。
  - [SQLite](https://www.sqlite.org/): 轻量级数据库，用于存储用户、消息和文件元数据。
  - [Uvicorn](https://www.uvicorn.org/): ASGI 服务器。
- **客户端 (Client)**:
  - [Click](https://click.palletsprojects.com/): 用于构建优雅的命令行接口。
  - [Cmd (Python standard library)](https://docs.python.org/3/library/cmd.html): 实现交互式 Shell 环境。
  - [Requests](https://requests.readthedocs.io/): 处理 HTTP 请求。

## 🚀 快速开始

### 1. 环境准备

确保您的系统中安装了 Python 3.10+。

```bash
# 克隆项目（假设）
git clone <repository_url>
cd MyHub
```

### 2. 启动服务端

服务端负责处理请求和数据存储。

```bash
cd server
# 安装依赖 (如果尚未安装)
pip install fastapi uvicorn click requests python-multipart

# 启动服务
python server.py
```

_服务端默认运行在 `http://127.0.0.1:8000`_

### 3. 启动客户端

打开一个新的终端窗口运行客户端。

```bash
cd client
# 启动客户端
python client.py
```

## 📖 使用指南

### 主菜单

启动客户端后，您将看到主菜单，支持以下命令：

- `login`: 登录现有账号。
- `register`: 注册新账号。
- `msg`: 进入消息留言板系统。
- `files`: 进入文件管理系统。
- `exit`: 退出程序。

### 消息系统 (`msg`)

进入 `msg` 模式后：

- **发布留言**: `post '内容'` (内容需用英文单引号包裹)
- **查看留言**:
  - `list`: 默认显示最近 4 条。
  - `list -n 10`: 显示最近 10 条。
  - `list --all`: 显示所有留言。
- **回复留言**: `reply <留言ID> '回复内容'`

### 文件系统 (`files`)

进入 `files` 模式后：

- **上传文件**: `upload <文件路径> [存储名称]`
  - 示例: `upload ./test.txt`
  - 示例: `upload ./test.txt my_renamed_file.txt`
- **查看列表**: `list` (显示文件 ID、名称、大小、上传者)
- **查看详情**: `look -id <文件ID>`
  - 进入文件详情页后，可以查看更详细的信息。
  - **文件留言**:
    - `msg '评论内容'`: 对当前文件发表评论。
    - `list`: 查看当前文件的评论。
  - `back`: 返回文件列表。

## 📂 项目结构

```
MyHub/
├── client/              # 客户端代码
│   ├── client.py        # 客户端入口与交互逻辑
│   └── .env             # 客户端配置（如服务器地址）
├── server/              # 服务端代码
│   ├── server.py        # FastAPI 应用入口与路由
│   ├── database.py      # 数据库连接与初始化
│   ├── utils.py         # 工具函数（如 Hash 处理）
│   ├── files/           # 上传文件的存储目录
│   └── MyHub.db         # SQLite 数据库文件
└── README.md            # 项目说明文档
```
