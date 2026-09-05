"""数据库连接管理。"""
from __future__ import annotations

import sqlite3
import threading
from pathlib import Path
from typing import Iterator

from ..config import DEFAULT_DB_PATH

_TERMINAL = object()

# FastAPI 的同步依赖与端点可能运行在不同线程池线程：
# 连接需允许跨线程（check_same_thread=False），
# 并用 WAL + busy_timeout 保证并发读写安全（多访客公开演示）。
_write_lock = threading.Lock()


def connect(db_path: Path | str | None = None) -> sqlite3.Connection:
    """打开 SQLite 连接（Row 工厂 + 外键 + 跨线程/WAL 安全）。"""
    path = Path(db_path) if db_path else DEFAULT_DB_PATH
    if path.parent and not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), check_same_thread=False, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 10000")
    conn.execute("PRAGMA synchronous = NORMAL")
    return conn


def execute(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> int:
    """写操作：进程级串行化，避免并发写冲突（demo 并发规模足够）。"""
    with _write_lock:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.lastrowid


def get_db(db_path: Path | str | None = None) -> Iterator[sqlite3.Connection]:
    """FastAPI 依赖：每个请求一个连接，异常回滚，正常提交。"""
    conn = connect(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def query_one(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> sqlite3.Row | None:
    return conn.execute(sql, params).fetchone()


def query_all(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
    return list(conn.execute(sql, params).fetchall())


def execute(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> int:
    cur = conn.execute(sql, params)
    conn.commit()
    return cur.lastrowid
