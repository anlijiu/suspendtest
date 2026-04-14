"""SuspendTestService 测试。"""

from __future__ import annotations

from dataclasses import dataclass

from core.interfaces import SleepMethod, StateDetector, WakeMethod
from core.models import (
    CommandResult,
    DetectorResult,
    PowerState,
    Subsystem,
)
from core.services.suspend_test_service import SuspendTestService


@dataclass(slots=True)
class FakeMethodResult:
    success: bool
    message: str


class FakeSleepMethod(SleepMethod):
    def __init__(self, result: FakeMethodResult) -> None:
        self._result = result

    @property
    def name(self) -> str:
        return "fake_sleep"

    def execute(self) -> CommandResult:
        return CommandResult(
            success=self._result.success,
            method_name=self.name,
            message=self._result.message,
            elapsed_seconds=0.01,
        )


class FakeWakeMethod(WakeMethod):
    def __init__(self, result: FakeMethodResult) -> None:
        self._result = result

    @property
    def name(self) -> str:
        return "fake_wake"

    def execute(self) -> CommandResult:
        return CommandResult(
            success=self._result.success,
            method_name=self.name,
            message=self._result.message,
            elapsed_seconds=0.01,
        )


class FakeDetector(StateDetector):
    def __init__(
        self,
        *,
        subsystem: Subsystem,
        sleep_reached: bool = True,
        wake_reached: bool = True,
    ) -> None:
        self._subsystem = subsystem
        self._sleep_reached = sleep_reached
        self._wake_reached = wake_reached

    @property
    def subsystem(self) -> Subsystem:
        return self._subsystem

    def wait_for_sleep(self, timeout_seconds: float) -> DetectorResult:
        return DetectorResult(
            subsystem=self._subsystem,
            target_state=PowerState.ASLEEP,
            reached=self._sleep_reached,
            elapsed_seconds=timeout_seconds / 10,
            message="sleep",
        )

    def wait_for_wake(self, timeout_seconds: float) -> DetectorResult:
        return DetectorResult(
            subsystem=self._subsystem,
            target_state=PowerState.AWAKE,
            reached=self._wake_reached,
            elapsed_seconds=timeout_seconds / 10,
            message="wake",
        )


def test_run_once_success() -> None:
    service = SuspendTestService(
        FakeSleepMethod(FakeMethodResult(success=True, message="ok")),
        FakeWakeMethod(FakeMethodResult(success=True, message="ok")),
        [
            FakeDetector(subsystem=Subsystem.MCU),
            FakeDetector(subsystem=Subsystem.SOC),
        ],
    )

    result = service.run_once(1, sleep_timeout_seconds=5.0, wake_timeout_seconds=5.0)

    assert result.success is True
    assert result.errors == []


def test_run_once_failed_when_soc_sleep_detection_failed() -> None:
    service = SuspendTestService(
        FakeSleepMethod(FakeMethodResult(success=True, message="ok")),
        FakeWakeMethod(FakeMethodResult(success=True, message="ok")),
        [
            FakeDetector(subsystem=Subsystem.MCU),
            FakeDetector(subsystem=Subsystem.SOC, sleep_reached=False),
        ],
    )

    result = service.run_once(1, sleep_timeout_seconds=5.0, wake_timeout_seconds=5.0)

    assert result.success is False
    assert any("soc 休眠检测失败" in err for err in result.errors)


def test_run_once_failed_when_sleep_command_failed() -> None:
    service = SuspendTestService(
        FakeSleepMethod(FakeMethodResult(success=False, message="send fail")),
        FakeWakeMethod(FakeMethodResult(success=True, message="ok")),
        [FakeDetector(subsystem=Subsystem.MCU), FakeDetector(subsystem=Subsystem.SOC)],
    )

    result = service.run_once(1, sleep_timeout_seconds=5.0, wake_timeout_seconds=5.0)

    assert result.success is False
    assert any("休眠命令发送失败" in err for err in result.errors)

