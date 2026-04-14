"""核心接口定义。"""

from __future__ import annotations

from abc import ABC, abstractmethod

from core.models import CommandResult, DetectorResult, RunReport, Subsystem


class SleepMethod(ABC):
    """休眠方法接口。"""

    @property
    @abstractmethod
    def name(self) -> str:
        """返回方法名称。"""

    @abstractmethod
    def execute(self) -> CommandResult:
        """执行休眠命令。

        Returns:
            CommandResult: 命令执行结果。
        """


class WakeMethod(ABC):
    """唤醒方法接口。"""

    @property
    @abstractmethod
    def name(self) -> str:
        """返回方法名称。"""

    @abstractmethod
    def execute(self) -> CommandResult:
        """执行唤醒命令。

        Returns:
            CommandResult: 命令执行结果。
        """


class StateDetector(ABC):
    """状态检测器接口。"""

    @property
    @abstractmethod
    def subsystem(self) -> Subsystem:
        """返回检测器所属子系统。"""

    @abstractmethod
    def wait_for_sleep(self, timeout_seconds: float) -> DetectorResult:
        """等待目标进入休眠状态。

        Args:
            timeout_seconds: 超时时间（秒）。

        Returns:
            DetectorResult: 检测结果。
        """

    @abstractmethod
    def wait_for_wake(self, timeout_seconds: float) -> DetectorResult:
        """等待目标进入唤醒状态。

        Args:
            timeout_seconds: 超时时间（秒）。

        Returns:
            DetectorResult: 检测结果。
        """


class ReportRenderer(ABC):
    """报告渲染器接口。"""

    @abstractmethod
    def render_markdown(self, report: RunReport, config_summary: dict[str, str]) -> str:
        """渲染 Markdown 报告。

        Args:
            report: 运行结果。
            config_summary: 配置摘要。

        Returns:
            str: Markdown 文本。
        """

