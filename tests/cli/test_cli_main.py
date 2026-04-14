"""CLI 测试。"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from click.testing import CliRunner

from cli import main as cli_main
from core.models import (
    CommandResult,
    CycleResult,
    DetectorResult,
    PowerState,
    RunReport,
    Subsystem,
)


def _write_default_config(path: Path) -> None:
    path.write_text(
        """
[can]
interface = zlgcan
channel = 0
bitrate = 500000
physical_id = 0x773
response_id = 0x7B3
functional_id = 0x7DF

[sleep.can_uds]
request_id = 0x773
request_data = 10 01

[wake.can_uds]
request_id = 0x773
request_data = 11 01

[detect.serial]
enabled = true
port = /dev/ttyUSB0
baudrate = 115200
silence_seconds = 0.5
poll_interval_seconds = 0.05

[detect.adb]
enabled = true
adb_path = adb
device_serial =
poll_interval_seconds = 0.5
command_timeout_seconds = 3.0

[timeouts]
sleep_timeout_seconds = 30
wake_timeout_seconds = 30
""".strip(),
        encoding="utf-8",
    )


class _FakeCycleRunner:
    def run(self, request, *, config_path: Path) -> RunReport:  # noqa: ANN001
        cycle_results = []
        for i in range(1, request.cycles + 1):
            cycle_results.append(
                CycleResult(
                    cycle_index=i,
                    sleep_command=CommandResult(True, "sleep", "ok", 0.1),
                    wake_command=CommandResult(True, "wake", "ok", 0.1),
                    sleep_detections={
                        Subsystem.MCU: DetectorResult(Subsystem.MCU, PowerState.ASLEEP, True, 0.2, "ok"),
                        Subsystem.SOC: DetectorResult(Subsystem.SOC, PowerState.ASLEEP, True, 0.2, "ok"),
                    },
                    wake_detections={
                        Subsystem.MCU: DetectorResult(Subsystem.MCU, PowerState.AWAKE, True, 0.2, "ok"),
                        Subsystem.SOC: DetectorResult(Subsystem.SOC, PowerState.AWAKE, True, 0.2, "ok"),
                    },
                    success=True,
                )
            )

        return RunReport(
            started_at=datetime.now(),
            finished_at=datetime.now(),
            config_path=config_path,
            total_cycles=request.cycles,
            successful_cycles=request.cycles,
            failed_cycles=0,
            cycle_results=cycle_results,
        )


class _FakeReportService:
    def write_report(self, report, *, config_summary, output_path=None):  # noqa: ANN001
        path = output_path or Path("result_2026_04_14.md")
        path.write_text("ok", encoding="utf-8")
        report.generated_report_path = path
        return path


def test_validate_config_command_success(tmp_path: Path) -> None:
    config_file = tmp_path / "config.ini"
    _write_default_config(config_file)

    result = CliRunner().invoke(cli_main.cli, ["validate-config", "--config", str(config_file)])

    assert result.exit_code == 0
    assert "配置校验通过" in result.output


def test_loop_command_success_with_fake_runtime(tmp_path: Path, monkeypatch) -> None:  # noqa: ANN001
    config_file = tmp_path / "config.ini"
    report_file = tmp_path / "result.md"
    _write_default_config(config_file)
    monkeypatch.setattr(cli_main, "_build_services", lambda _cfg: (_FakeCycleRunner(), _FakeReportService()))

    result = CliRunner().invoke(
        cli_main.cli,
        [
            "loop",
            "--config",
            str(config_file),
            "--cycles",
            "2",
            "--report",
            str(report_file),
        ],
    )

    assert result.exit_code == 0
    assert report_file.exists()
    assert "循环测试完成" in result.output

