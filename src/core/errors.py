"""核心异常定义。"""

from __future__ import annotations


class SuspendTestError(Exception):
    """项目基础异常。

    Args:
        message: 面向用户的错误信息。
        hint: 可选的修复建议。
    """

    def __init__(self, message: str, *, hint: str | None = None) -> None:
        super().__init__(message)
        self.hint = hint


class ConfigError(SuspendTestError):
    """配置解析或校验异常。"""


class CommandExecutionError(SuspendTestError):
    """命令执行失败异常。"""


class DetectionError(SuspendTestError):
    """状态检测执行失败异常。"""

