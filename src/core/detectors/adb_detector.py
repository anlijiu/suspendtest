"""ADB SOC 状态检测器。"""

from __future__ import annotations

import subprocess
from time import monotonic, sleep
from typing import Callable

from core.interfaces import StateDetector
from core.models import AdbDetectorConfig, DetectorResult, PowerState, Subsystem

Runner = Callable[..., subprocess.CompletedProcess[str]]


class AdbSocSleepDetector(StateDetector):
    """通过 ADB 连接状态判断 SOC 休眠/唤醒。"""

    def __init__(
        self,
        config: AdbDetectorConfig,
        *,
        runner: Runner = subprocess.run,
        monotonic_fn: Callable[[], float] = monotonic,
        sleep_fn: Callable[[float], None] = sleep,
    ) -> None:
        """初始化 ADB 检测器。

        Args:
            config: ADB 检测配置。
            runner: 子进程调用函数，可注入用于测试。
            monotonic_fn: 单调时钟函数。
            sleep_fn: 休眠函数。
        """
        self._config = config
        self._runner = runner
        self._monotonic = monotonic_fn
        self._sleep_fn = sleep_fn

    @property
    def subsystem(self) -> Subsystem:
        return Subsystem.SOC

    def wait_for_sleep(self, timeout_seconds: float) -> DetectorResult:
        """等待 SOC 进入休眠（ADB 不可达）。"""
        started = self._monotonic()
        while self._monotonic() - started <= timeout_seconds:
            connected, detail = self._is_connected()
            if not connected:
                return DetectorResult(
                    subsystem=self.subsystem,
                    target_state=PowerState.ASLEEP,
                    reached=True,
                    elapsed_seconds=self._monotonic() - started,
                    message=f"ADB 不可达，判定 SOC 已休眠（{detail}）。",
                )
            self._sleep_fn(self._config.poll_interval_seconds)
        return DetectorResult(
            subsystem=self.subsystem,
            target_state=PowerState.ASLEEP,
            reached=False,
            elapsed_seconds=self._monotonic() - started,
            message=f"超时 {timeout_seconds:.1f}s SOC 仍可通过 ADB 访问。",
        )

    def wait_for_wake(self, timeout_seconds: float) -> DetectorResult:
        """等待 SOC 唤醒（ADB 可达）。"""
        started = self._monotonic()
        while self._monotonic() - started <= timeout_seconds:
            connected, detail = self._is_connected()
            if connected:
                return DetectorResult(
                    subsystem=self.subsystem,
                    target_state=PowerState.AWAKE,
                    reached=True,
                    elapsed_seconds=self._monotonic() - started,
                    message=f"ADB 可达，判定 SOC 已唤醒（{detail}）。",
                )
            self._sleep_fn(self._config.poll_interval_seconds)
        return DetectorResult(
            subsystem=self.subsystem,
            target_state=PowerState.AWAKE,
            reached=False,
            elapsed_seconds=self._monotonic() - started,
            message=f"超时 {timeout_seconds:.1f}s SOC 仍不可通过 ADB 访问。",
        )

    def _is_connected(self) -> tuple[bool, str]:
        cmd = [self._config.adb_path]
        if self._config.device_serial:
            cmd.extend(["-s", self._config.device_serial])
        cmd.extend(["get-state"])

        try:
            completed = self._runner(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                timeout=self._config.command_timeout_seconds,
            )
        except FileNotFoundError:
            return False, "adb 不存在"
        except subprocess.TimeoutExpired:
            return False, "adb 命令超时"
        except Exception as exc:  # noqa: BLE001
            return False, f"adb 异常: {exc}"

        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip() or f"code={completed.returncode}"
            return False, detail

        state = completed.stdout.strip().lower()
        return state == "device", state or "unknown"

