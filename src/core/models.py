"""核心数据模型。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path


class SleepMethodType(str, Enum):
    """休眠方式类型。"""

    CAN_UDS = "can_uds"


class WakeMethodType(str, Enum):
    """唤醒方式类型。"""

    CAN_UDS = "can_uds"


class Subsystem(str, Enum):
    """被检测子系统类型。"""

    MCU = "mcu"
    SOC = "soc"


class PowerState(str, Enum):
    """电源状态。"""

    AWAKE = "awake"
    ASLEEP = "asleep"


class CyclePhase(str, Enum):
    """单轮流程状态机阶段。"""

    IDLE = "idle"
    SENDING_SLEEP = "sending_sleep"
    WAITING_SLEEP = "waiting_sleep"
    SLEEPING = "sleeping"
    SENDING_WAKE = "sending_wake"
    WAITING_WAKE = "waiting_wake"
    AWAKE = "awake"
    FINISHED = "finished"
    FAILED = "failed"


@dataclass(slots=True)
class CanConfig:
    """CAN 总线配置。"""

    interface: str
    channel: int
    bitrate: int
    device_type: str
    device_index: int
    libpath: str
    resistance: bool
    physical_id: int
    response_id: int
    functional_id: int


@dataclass(slots=True)
class CanUdsMethodConfig:
    """CAN UDS 命令配置。"""

    request_id: int
    request_data: bytes


@dataclass(slots=True)
class SerialDetectorConfig:
    """串口检测器配置。"""

    enabled: bool
    port: str
    baudrate: int
    silence_seconds: float = 0.5
    poll_interval_seconds: float = 0.05


@dataclass(slots=True)
class AdbDetectorConfig:
    """ADB 检测器配置。"""

    enabled: bool
    adb_path: str = "adb"
    device_serial: str | None = None
    poll_interval_seconds: float = 0.5
    command_timeout_seconds: float = 3.0


@dataclass(slots=True)
class TimeoutConfig:
    """流程超时配置。"""

    sleep_timeout_seconds: float = 30.0
    wake_timeout_seconds: float = 30.0


@dataclass(slots=True)
class SuspendTestConfig:
    """测试总配置。"""

    can: CanConfig
    sleep_can_uds: CanUdsMethodConfig
    wake_can_uds: CanUdsMethodConfig
    serial_detector: SerialDetectorConfig
    adb_detector: AdbDetectorConfig
    timeouts: TimeoutConfig
    config_path: Path

    def summary(self) -> dict[str, str]:
        """生成报告可用的配置摘要。

        Returns:
            dict[str, str]: 可读配置摘要。
        """
        return {
            "config_path": str(self.config_path),
            "can.interface": self.can.interface,
            "can.channel": str(self.can.channel),
            "can.bitrate": str(self.can.bitrate),
            "can.device_type": self.can.device_type,
            "can.device_index": str(self.can.device_index),
            "can.libpath": self.can.libpath,
            "can.resistance": str(self.can.resistance),
            "can.physical_id": f"0x{self.can.physical_id:X}",
            "can.response_id": f"0x{self.can.response_id:X}",
            "can.functional_id": f"0x{self.can.functional_id:X}",
            "serial.enabled": str(self.serial_detector.enabled),
            "serial.port": self.serial_detector.port,
            "serial.baudrate": str(self.serial_detector.baudrate),
            "adb.enabled": str(self.adb_detector.enabled),
            "adb.path": self.adb_detector.adb_path,
            "adb.device_serial": self.adb_detector.device_serial or "",
        }


@dataclass(slots=True)
class CommandResult:
    """命令执行结果。"""

    success: bool
    method_name: str
    message: str
    elapsed_seconds: float


@dataclass(slots=True)
class DetectorResult:
    """检测结果。"""

    subsystem: Subsystem
    target_state: PowerState
    reached: bool
    elapsed_seconds: float
    message: str


@dataclass(slots=True)
class CycleResult:
    """单轮休眠/唤醒结果。"""

    cycle_index: int
    sleep_command: CommandResult
    wake_command: CommandResult
    sleep_detections: dict[Subsystem, DetectorResult]
    wake_detections: dict[Subsystem, DetectorResult]
    success: bool
    errors: list[str] = field(default_factory=list)
    phase_history: list[CyclePhase] = field(default_factory=list)


@dataclass(slots=True)
class SuspendCycleRequest:
    """循环执行请求参数。"""

    cycles: int
    sleep_timeout_seconds: float
    wake_timeout_seconds: float


@dataclass(slots=True)
class RunReport:
    """循环执行汇总报告。"""

    started_at: datetime
    finished_at: datetime
    config_path: Path
    total_cycles: int
    successful_cycles: int
    failed_cycles: int
    cycle_results: list[CycleResult]
    generated_report_path: Path | None = None
