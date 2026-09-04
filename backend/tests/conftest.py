"""共享 fixture：每个用例使用独立临时数据库。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from app.db.init_db import init_db


@pytest.fixture
def conn(tmp_path):
    db_path = tmp_path / "oksleep_test.db"
    c = init_db(db_path)
    yield c
    c.close()
