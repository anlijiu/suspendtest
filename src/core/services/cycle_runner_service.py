"""循环执行服务。"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from core.errors import ConfigError
from core.models import RunReport, SuspendCycleRequest
from core.services.suspend_test_service import SuspendTestService


class CycleRunnerService:
    """负责 N 次循环的执行与统计。"""

    def __init__(self, suspend_test_service: SuspendTestService) -> None:
        self._suspend_test_service = suspend_test_service

    def run(self, request: SuspendCycleRequest, *, config_path: Path) -> RunReport:
        """执行循环测试。

        Args:
            request: 循环请求。
            config_path: 配置文件路径。

        Returns:
            RunReport: 汇总报告对象。
        """
        if request.cycles <= 0:
            raise ConfigError("cycles 必须大于 0。")

        started_at = datetime.now()
        cycle_results = []
        for cycle_index in range(1, request.cycles + 1):
            cycle_result = self._suspend_test_service.run_once(
                cycle_index,
                sleep_timeout_seconds=request.sleep_timeout_seconds,
                wake_timeout_seconds=request.wake_timeout_seconds,
            )
            cycle_results.append(cycle_result)

        successful_cycles = sum(1 for item in cycle_results if item.success)
        failed_cycles = request.cycles - successful_cycles

        return RunReport(
            started_at=started_at,
            finished_at=datetime.now(),
            config_path=config_path,
            total_cycles=request.cycles,
            successful_cycles=successful_cycles,
            failed_cycles=failed_cycles,
            cycle_results=cycle_results,
        )

