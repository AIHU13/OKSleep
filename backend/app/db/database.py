"""数据库连接管理。"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterator

from ..config import DEFAULT_DB_PATH

_TERMINAL = object()


def connect(db_path: Path | str | None = None) -> sqlite3.Connection:
    """打开 SQLite 连接（Row 工厂 + 外键）。"""
    path = Path(db_path) if db_path else DEFAULT_DB_PATH
    if path.parent and not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


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
