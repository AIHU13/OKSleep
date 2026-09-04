"""业务规则错误：Rule Engine 不允许的操作（路由层转 HTTP 409）。"""
from __future__ import annotations


class RuleError(Exception):
    """规则引擎拒绝的操作。code 用于前端提示归类。"""

    def __init__(self, message: str, code: str = "rule_error", http_status: int = 409):
        super().__init__(message)
        self.message = message
        self.code = code
        self.http_status = http_status
