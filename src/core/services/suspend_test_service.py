"""单轮休眠/唤醒编排服务。"""

from __future__ import annotations

from core.interfaces import SleepMethod, StateDetector, WakeMethod
from core.models import (
    CyclePhase,
    CycleResult,
    DetectorResult,
    PowerState,
    Subsystem,
)
from core.state_machine import CycleStateMachine


class SuspendTestService:
    """执行单轮休眠/唤醒流程。"""

    def __init__(self, sleep_method: SleepMethod, wake_method: WakeMethod, detectors: list[StateDetector]) -> None:
        """初始化编排服务。

        Args:
            sleep_method: 休眠方法实现。
            wake_method: 唤醒方法实现。
            detectors: 状态检测器列表。
        """
        self._sleep_method = sleep_method
        self._wake_method = wake_method
        self._detectors = detectors

    def run_once(self, cycle_index: int, *, sleep_timeout_seconds: float, wake_timeout_seconds: float) -> CycleResult:
        """运行一轮休眠/唤醒测试。

        Args:
            cycle_index: 当前轮次（1-based）。
            sleep_timeout_seconds: 休眠检测超时。
            wake_timeout_seconds: 唤醒检测超时。

        Returns:
            CycleResult: 单轮执行结果。
        """
        errors: list[str] = []
        state_machine = CycleStateMachine()

        state_machine.transit(CyclePhase.SENDING_SLEEP)
        sleep_command = self._sleep_method.execute()
        sleep_results: dict[Subsystem, DetectorResult] = {}
        if sleep_command.success:
            state_machine.transit(CyclePhase.WAITING_SLEEP)
            sleep_results = self._run_detectors(target=PowerState.ASLEEP, timeout_seconds=sleep_timeout_seconds)
            if all(result.reached for result in sleep_results.values()):
                state_machine.transit(CyclePhase.SLEEPING)
            errors.extend(
                f"{result.subsystem.value} 休眠检测失败: {result.message}"
                for result in sleep_results.values()
                if not result.reached
            )
        else:
            errors.append(f"休眠命令发送失败: {sleep_command.message}")
            sleep_results = self._placeholder_results(PowerState.ASLEEP, "休眠命令失败，跳过休眠检测。")

        state_machine.transit(CyclePhase.SENDING_WAKE)
        wake_command = self._wake_method.execute()
        wake_results: dict[Subsystem, DetectorResult] = {}
        if wake_command.success:
            state_machine.transit(CyclePhase.WAITING_WAKE)
            wake_results = self._run_detectors(target=PowerState.AWAKE, timeout_seconds=wake_timeout_seconds)
            if all(result.reached for result in wake_results.values()):
                state_machine.transit(CyclePhase.AWAKE)
            errors.extend(
                f"{result.subsystem.value} 唤醒检测失败: {result.message}"
                for result in wake_results.values()
                if not result.reached
            )
        else:
            errors.append(f"唤醒命令发送失败: {wake_command.message}")
            wake_results = self._placeholder_results(PowerState.AWAKE, "唤醒命令失败，跳过唤醒检测。")

        all_sleep_ok = all(result.reached for result in sleep_results.values())
        all_wake_ok = all(result.reached for result in wake_results.values())
        success = sleep_command.success and wake_command.success and all_sleep_ok and all_wake_ok
        state_machine.transit(CyclePhase.FINISHED if success else CyclePhase.FAILED)

        return CycleResult(
            cycle_index=cycle_index,
            sleep_command=sleep_command,
            wake_command=wake_command,
            sleep_detections=sleep_results,
            wake_detections=wake_results,
            success=success,
            errors=errors,
            phase_history=state_machine.phase_history,
        )

    def _run_detectors(self, *, target: PowerState, timeout_seconds: float) -> dict[Subsystem, DetectorResult]:
        results: dict[Subsystem, DetectorResult] = {}
        for detector in self._detectors:
            if target is PowerState.ASLEEP:
                result = detector.wait_for_sleep(timeout_seconds)
            else:
                result = detector.wait_for_wake(timeout_seconds)
            results[detector.subsystem] = result
        return results

    def _placeholder_results(self, target: PowerState, message: str) -> dict[Subsystem, DetectorResult]:
        return {
            detector.subsystem: DetectorResult(
                subsystem=detector.subsystem,
                target_state=target,
                reached=False,
                elapsed_seconds=0.0,
                message=message,
            )
            for detector in self._detectors
        }
