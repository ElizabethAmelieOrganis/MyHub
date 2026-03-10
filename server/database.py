#!/usr/bin/env python3
"""
MyHub数据库模块,使用SQLite进行单文件存储
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from utils import println_success

DB_PATH = Path("MyHub.db")


@contextmanager
def get_db():
    """
    获取数据库连接
    使用方式:
        with get_db() as conn:
            conn.execute(...)
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    """初始化数据库"""
    with get_db() as conn:
        """创建表"""
        conn.executescript("""
                CREATE TABLE IF NOT EXISTS files(
                    id integer primary key autoincrement,
                    original_name text not null,
                    stored_name text not null unique,
                    size integer not null,
                    uploader text not null,
                    upload_time text not null,
                    tags text default ""
                );
                CREATE TABLE IF NOT EXISTS messages(
                    id integer primary key autoincrement,
                    content text not null,
                    author text not null,
                    file_id integer,
                    created_at text not null,
                    foreign key(file_id) references files(id) on delete cascade
                );
                """)
        """创建索引"""
        conn.executescript("""
            CREATE INDEX IF NOT EXISTS idx_file_time ON files(upload_time);
            """)
        conn.executescript("""
            CREATE INDEX IF NOT EXISTS idx_msgs_file ON messages(file_id);
            """)
    println_success(f"√ 数据库初始化完成{DB_PATH.absolute()}")


if __name__ == "__main__":
    init_db()
