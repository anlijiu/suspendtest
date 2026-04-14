"""CAN UDS 休眠/唤醒命令实现。"""

from __future__ import annotations

from time import monotonic
from typing import Any, Callable

from core.interfaces import SleepMethod, WakeMethod
from core.models import CanConfig, CanUdsMethodConfig, CommandResult

BusFactory = Callable[..., Any]


class CanUdsCommandService:
    """CAN UDS 报文发送服务。"""

    def __init__(
        self,
        can_config: CanConfig,
        *,
        bus_factory: BusFactory | None = None,
        monotonic_fn: Callable[[], float] = monotonic,
    ) -> None:
        """初始化 CAN UDS 发送服务。

        Args:
            can_config: CAN 总线配置。
            bus_factory: 可注入的总线工厂，用于测试替换。
            monotonic_fn: 单调时钟函数。
        """
        self._can_config = can_config
        self._bus_factory = bus_factory or self._default_bus_factory
        self._monotonic = monotonic_fn

    def send(self, method_name: str, *, request_id: int, request_data: bytes) -> CommandResult:
        """发送一条 CAN UDS 请求。

        Args:
            method_name: 方法名（用于报告）。
            request_id: 发送 ID。
            request_data: 发送负载。

        Returns:
            CommandResult: 发送结果。
        """
        started = self._monotonic()
        bus: Any | None = None
        try:
            import can

            bus = self._bus_factory(**self._bus_kwargs())
            message = can.Message(
                arbitration_id=request_id,
                is_extended_id=False,
                data=request_data,
                channel=self._can_config.channel,
            )
            bus.send(message)
            elapsed = self._monotonic() - started
            payload = " ".join(f"{byte:02X}" for byte in request_data)
            return CommandResult(
                success=True,
                method_name=method_name,
                message=f"发送成功: id=0x{request_id:X}, data={payload}",
                elapsed_seconds=elapsed,
            )
        except Exception as exc:  # noqa: BLE001
            elapsed = self._monotonic() - started
            return CommandResult(
                success=False,
                method_name=method_name,
                message=f"发送失败: {exc}",
                elapsed_seconds=elapsed,
            )
        finally:
            if bus is not None and hasattr(bus, "shutdown"):
                bus.shutdown()

    @staticmethod
    def _default_bus_factory(**kwargs: Any) -> Any:
        import can

        return can.interface.Bus(**kwargs)

    def _bus_kwargs(self) -> dict[str, Any]:
        interface = self._can_config.interface.strip().lower()
        if interface == "zlgcan":
            channel_count = max(self._can_config.channel + 1, 1)
            return {
                "interface": "zlgcan",
                "channel": self._can_config.channel,
                "device_type": self._resolve_zlgcan_device_type(self._can_config.device_type),
                "device_index": self._can_config.device_index,
                "libpath": self._can_config.libpath,
                "configs": [
                    {
                        "bitrate": self._can_config.bitrate,
                        "resistance": 1 if self._can_config.resistance else 0,
                    }
                    for _ in range(channel_count)
                ],
            }
        return {
            "interface": self._can_config.interface,
            "channel": self._can_config.channel,
            "bitrate": self._can_config.bitrate,
        }

    @staticmethod
    def _resolve_zlgcan_device_type(device_type: str) -> int:
        import zlgcan

        if not hasattr(zlgcan.ZCANDeviceType, device_type):
            valid = [name for name in dir(zlgcan.ZCANDeviceType) if name.startswith("ZCAN_")]
            preview = ", ".join(valid[:8])
            raise ValueError(f"未知 zlgcan device_type: {device_type}，例如: {preview}")
        return int(getattr(zlgcan.ZCANDeviceType, device_type))


class CanUdsSleepMethod(SleepMethod):
    """通过 CAN UDS 发送休眠命令。"""

    def __init__(self, command_service: CanUdsCommandService, config: CanUdsMethodConfig) -> None:
        self._command_service = command_service
        self._config = config

    @property
    def name(self) -> str:
        return "can_uds"

    def execute(self) -> CommandResult:
        """执行休眠命令。"""
        return self._command_service.send(
            "can_uds_sleep",
            request_id=self._config.request_id,
            request_data=self._config.request_data,
        )


class CanUdsWakeMethod(WakeMethod):
    """通过 CAN UDS 发送唤醒命令。"""

    def __init__(self, command_service: CanUdsCommandService, config: CanUdsMethodConfig) -> None:
        self._command_service = command_service
        self._config = config

    @property
    def name(self) -> str:
        return "can_uds"

    def execute(self) -> CommandResult:
        """执行唤醒命令。"""
        return self._command_service.send(
            "can_uds_wake",
            request_id=self._config.request_id,
            request_data=self._config.request_data,
        )
