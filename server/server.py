#!/usr/bin/env python3
"""
MyHub服务端
"""

from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

from database import get_db, init_db
from fastapi import FastAPI, Header, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from utils import println_failed, println_success

# ==========配置文件==========
FILES_DIR = Path("./files")
FILES_DIR.mkdir(exist_ok=True)
# 可用token
USERS = {"HY-token": {"name": "HY"}, "LCY-token": {"name": "LCY"}}


# ==========数据模型==========
class PostBody(BaseModel):
    data: str
    file_id: Optional[int] = None


class ListBody(BaseModel):
    limit: int = 4
    file_id: Optional[int] = None


class FileIdBody(BaseModel):
    file_id: int


# ==========服务启动项==========
@asynccontextmanager
async def start_up(app: FastAPI):
    try:
        init_db()
        yield
        println_success("服务已终止")
    except Exception as e:
        println_failed(f"服务端启动错误:{e}")


def verify_token(token: str | None) -> str:
    """
    验证用户令牌
    失败时抛出 403 错误
    """
    if token not in USERS:
        raise HTTPException(status_code=403, detail="无效的认证令牌")
    user = USERS[token]["name"]
    return user


app = FastAPI(title="MyHub", version="1.0.0", lifespan=start_up)

# ==========路由==========


@app.get("/")
async def index():
    """服务端健康检查"""
    return {"status": "ok", "service": "MyHub", "version": "1.0.0"}


@app.post("/headers")
async def headers(token: str | None = Header(None)):
    """检查测试请求头"""
    print(verify_token(token))
    return {"status": "ok"}


# ==========留言系统路由==========
@app.post("/msg/create")
async def post_messages(body: PostBody, token: str | None = Header(None)):
    file_id = body.file_id
    content = body.data
    if content == "":
        raise HTTPException(status_code=400, detail="留言不可为空")
    user = verify_token(token)
    with get_db() as conn:
        conn.execute(
            """INSERT INTO messages(content,author,file_id,created_at)
                        VALUES (?,?,?,?)""",
            (content, user, file_id, datetime.now().isoformat()),
        )
    return {"message": "留言成功"}

@app.post("/msg/list")
async def get_messages(body: ListBody, token: str | None = Header(None)):
    verify_token(token)
    limit = body.limit
    file_id = body.file_id
    
    with get_db() as conn:
        sql = "SELECT id,content,author,file_id,created_at FROM messages WHERE "
        params = []
        
        if file_id is not None:
            sql += "file_id = ? "
            params.append(file_id)
        else:
            sql += "file_id IS NULL "
            
        sql += "ORDER BY id DESC"
        
        if limit > 0:
            sql += " LIMIT ?"
            params.append(limit)
            
        rows = conn.execute(sql, params).fetchall()
    return [dict(row) for row in rows]


# ==========文件系统路由==========
@app.post("/file/upload")
async def upload_file(
    file: UploadFile = File(...),
    stored_name: Optional[str] = Form(None),
    token: str | None = Header(None)
):
    user = verify_token(token)
    
    final_stored_name = stored_name if stored_name else file.filename
    
    # 检查文件名是否已存在
    with get_db() as conn:
        exists = conn.execute(
            "SELECT 1 FROM files WHERE stored_name = ?", 
            (final_stored_name,)
        ).fetchone()
        if exists:
            raise HTTPException(status_code=400, detail=f"文件存储名称 '{final_stored_name}' 已存在")
    
    file_path = FILES_DIR / final_stored_name
    
    try:
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {e}")
        
    with get_db() as conn:
        conn.execute(
            """INSERT INTO files(original_name, stored_name, size, uploader, upload_time)
               VALUES (?, ?, ?, ?, ?)""",
            (file.filename, final_stored_name, len(contents), user, datetime.now().isoformat())
        )
        
    return {"message": "文件上传成功", "stored_name": final_stored_name}


@app.post("/file/list")
async def list_files(token: str | None = Header(None)):
    verify_token(token)
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, original_name, stored_name, size, uploader, upload_time FROM files ORDER BY id DESC"
        ).fetchall()
    return [dict(row) for row in rows]


@app.post("/file/detail")
async def get_file_detail(body: FileIdBody, token: str | None = Header(None)):
    verify_token(token)
    file_id = body.file_id
    with get_db() as conn:
        row = conn.execute(
            "SELECT id, original_name, stored_name, size, uploader, upload_time, tags FROM files WHERE id = ?",
            (file_id,)
        ).fetchone()
        
    if not row:
        raise HTTPException(status_code=404, detail="文件不存在")
        
    return dict(row)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
