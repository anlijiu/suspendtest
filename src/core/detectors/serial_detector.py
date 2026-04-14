"""串口 MCU 状态检测器。"""

from __future__ import annotations

from time import monotonic, sleep
from typing import Any, Callable

from core.interfaces import StateDetector
from core.models import DetectorResult, PowerState, SerialDetectorConfig, Subsystem

SerialFactory = Callable[..., Any]


class SerialMcuSleepDetector(StateDetector):
    """通过串口数据静默判断 MCU 休眠状态。"""

    def __init__(
        self,
        config: SerialDetectorConfig,
        *,
        serial_factory: SerialFactory | None = None,
        monotonic_fn: Callable[[], float] = monotonic,
        sleep_fn: Callable[[float], None] = sleep,
    ) -> None:
        """初始化串口检测器。

        Args:
            config: 串口检测配置。
            serial_factory: 可注入串口工厂，便于测试。
            monotonic_fn: 单调时钟函数。
            sleep_fn: 休眠函数。
        """
        self._config = config
        self._monotonic = monotonic_fn
        self._sleep_fn = sleep_fn
        self._serial_factory = serial_factory or self._default_serial_factory
        self._port: Any | None = None

    @property
    def subsystem(self) -> Subsystem:
        return Subsystem.MCU

    def wait_for_sleep(self, timeout_seconds: float) -> DetectorResult:
        """等待 MCU 进入休眠（串口静默）。"""
        started = self._monotonic()
        last_data = started
        try:
            while self._monotonic() - started <= timeout_seconds:
                if self._consume_if_has_data():
                    last_data = self._monotonic()
                elif self._monotonic() - last_data >= self._config.silence_seconds:
                    elapsed = self._monotonic() - started
                    return DetectorResult(
                        subsystem=self.subsystem,
                        target_state=PowerState.ASLEEP,
                        reached=True,
                        elapsed_seconds=elapsed,
                        message=f"串口静默达到 {self._config.silence_seconds:.3f}s，判定 MCU 已休眠。",
                    )
                self._sleep_fn(self._config.poll_interval_seconds)
        except Exception as exc:  # noqa: BLE001
            return DetectorResult(
                subsystem=self.subsystem,
                target_state=PowerState.ASLEEP,
                reached=False,
                elapsed_seconds=self._monotonic() - started,
                message=f"串口检测异常: {exc}",
            )

        return DetectorResult(
            subsystem=self.subsystem,
            target_state=PowerState.ASLEEP,
            reached=False,
            elapsed_seconds=self._monotonic() - started,
            message=f"超时 {timeout_seconds:.1f}s 未达到串口静默阈值。",
        )

    def wait_for_wake(self, timeout_seconds: float) -> DetectorResult:
        """等待 MCU 唤醒（串口恢复数据）。"""
        started = self._monotonic()
        try:
            while self._monotonic() - started <= timeout_seconds:
                if self._consume_if_has_data():
                    return DetectorResult(
                        subsystem=self.subsystem,
                        target_state=PowerState.AWAKE,
                        reached=True,
                        elapsed_seconds=self._monotonic() - started,
                        message="串口恢复数据，判定 MCU 已唤醒。",
                    )
                self._sleep_fn(self._config.poll_interval_seconds)
        except Exception as exc:  # noqa: BLE001
            return DetectorResult(
                subsystem=self.subsystem,
                target_state=PowerState.AWAKE,
                reached=False,
                elapsed_seconds=self._monotonic() - started,
                message=f"串口检测异常: {exc}",
            )

        return DetectorResult(
            subsystem=self.subsystem,
            target_state=PowerState.AWAKE,
            reached=False,
            elapsed_seconds=self._monotonic() - started,
            message=f"超时 {timeout_seconds:.1f}s 未检测到串口数据恢复。",
        )

    def _consume_if_has_data(self) -> bool:
        port = self._ensure_port()
        waiting = int(getattr(port, "in_waiting", 0))
        if waiting <= 0:
            return False
        port.read(waiting)
        return True

    def _ensure_port(self) -> Any:
        if self._port is None:
            self._port = self._serial_factory(
                self._config.port,
                self._config.baudrate,
                timeout=0,
            )
        return self._port

    @staticmethod
    def _default_serial_factory(*args: Any, **kwargs: Any) -> Any:
        import serial

        return serial.Serial(*args, **kwargs)

