"""Markdown 报告服务。"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Mapping

from core.interfaces import ReportRenderer
from core.models import CycleResult, DetectorResult, RunReport, Subsystem


class ReportService(ReportRenderer):
    """负责生成 Markdown 结果报告。"""

    def render_markdown(self, report: RunReport, config_summary: dict[str, str]) -> str:
        """渲染 Markdown 报告。"""
        lines: list[str] = []
        lines.append("# 休眠唤醒测试报告")
        lines.append("")
        lines.append("## 执行信息")
        lines.append("")
        lines.append(f"- 开始时间: {report.started_at.isoformat(timespec='seconds')}")
        lines.append(f"- 结束时间: {report.finished_at.isoformat(timespec='seconds')}")
        lines.append(f"- 配置文件: `{report.config_path}`")
        lines.append(f"- 总轮次: {report.total_cycles}")
        lines.append(f"- 成功轮次: {report.successful_cycles}")
        lines.append(f"- 失败轮次: {report.failed_cycles}")
        lines.append("")
        lines.append("## 配置摘要")
        lines.append("")
        for key in sorted(config_summary):
            lines.append(f"- {key}: `{config_summary[key]}`")
        lines.append("")
        lines.append("## 每轮结果")
        lines.append("")
        lines.append(
            "| 轮次 | 成功 | 休眠命令 | MCU休眠 | SOC休眠 | 唤醒命令 | MCU唤醒 | SOC唤醒 | 失败原因 |"
        )
        lines.append("|---:|:---:|---|---|---|---|---|---|---|")
        for cycle in report.cycle_results:
            lines.append(self._render_cycle_row(cycle))
        lines.append("")
        lines.append("## 失败详情")
        lines.append("")
        failed = [item for item in report.cycle_results if not item.success]
        if not failed:
            lines.append("- 无失败轮次。")
        else:
            for item in failed:
                lines.append(f"### 轮次 {item.cycle_index}")
                lines.extend(f"- {err}" for err in item.errors)
                lines.append("")
        return "\n".join(lines).strip() + "\n"

    def write_report(
        self,
        report: RunReport,
        *,
        config_summary: dict[str, str],
        output_path: Path | None = None,
    ) -> Path:
        """写入报告文件。

        Args:
            report: 运行结果。
            config_summary: 配置摘要。
            output_path: 可选输出路径。

        Returns:
            Path: 写入后的路径。
        """
        destination = output_path or Path(self._default_report_name())
        destination.write_text(
            self.render_markdown(report, config_summary=config_summary),
            encoding="utf-8",
        )
        report.generated_report_path = destination
        return destination

    @staticmethod
    def _default_report_name() -> str:
        now = datetime.now()
        return f"result_{now:%Y_%m_%d}.md"

    @staticmethod
    def _render_cycle_row(cycle: CycleResult) -> str:
        mcu_sleep = ReportService._status(cycle.sleep_detections, Subsystem.MCU)
        soc_sleep = ReportService._status(cycle.sleep_detections, Subsystem.SOC)
        mcu_wake = ReportService._status(cycle.wake_detections, Subsystem.MCU)
        soc_wake = ReportService._status(cycle.wake_detections, Subsystem.SOC)
        errors = "<br>".join(cycle.errors) if cycle.errors else "-"
        return (
            f"| {cycle.cycle_index} | {'✅' if cycle.success else '❌'} "
            f"| {cycle.sleep_command.message} | {mcu_sleep} | {soc_sleep} "
            f"| {cycle.wake_command.message} | {mcu_wake} | {soc_wake} | {errors} |"
        )

    @staticmethod
    def _status(results: Mapping[Subsystem, DetectorResult], subsystem: Subsystem) -> str:
        detector = results.get(subsystem)
        if detector is None:
            return "N/A"
        reached = "✅" if detector.reached else "❌"
        elapsed = detector.elapsed_seconds
        return f"{reached} ({elapsed:.2f}s)"
