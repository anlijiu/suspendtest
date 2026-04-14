"""ReportService 测试。"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from core.models import (
    CommandResult,
    CycleResult,
    DetectorResult,
    PowerState,
    RunReport,
    Subsystem,
)
from core.services.report_service import ReportService


def test_write_report_generates_markdown_file(tmp_path: Path) -> None:
    report = RunReport(
        started_at=datetime(2026, 4, 14, 10, 0, 0),
        finished_at=datetime(2026, 4, 14, 10, 0, 10),
        config_path=Path("config.ini"),
        total_cycles=1,
        successful_cycles=1,
        failed_cycles=0,
        cycle_results=[
            CycleResult(
                cycle_index=1,
                sleep_command=CommandResult(True, "sleep", "sleep ok", 0.1),
                wake_command=CommandResult(True, "wake", "wake ok", 0.1),
                sleep_detections={
                    Subsystem.MCU: DetectorResult(Subsystem.MCU, PowerState.ASLEEP, True, 1.0, "ok"),
                    Subsystem.SOC: DetectorResult(Subsystem.SOC, PowerState.ASLEEP, True, 1.2, "ok"),
                },
                wake_detections={
                    Subsystem.MCU: DetectorResult(Subsystem.MCU, PowerState.AWAKE, True, 0.8, "ok"),
                    Subsystem.SOC: DetectorResult(Subsystem.SOC, PowerState.AWAKE, True, 0.7, "ok"),
                },
                success=True,
            )
        ],
    )

    path = tmp_path / "result_2026_04_14.md"
    saved_path = ReportService().write_report(
        report,
        config_summary={"can.channel": "0"},
        output_path=path,
    )

    content = saved_path.read_text(encoding="utf-8")
    assert saved_path == path
    assert "休眠唤醒测试报告" in content
    assert "| 1 | ✅" in content

