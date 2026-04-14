"""CLI 入口。"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import click

from core.config_service import ConfigService
from core.detectors import AdbSocSleepDetector, SerialMcuSleepDetector
from core.errors import SuspendTestError
from core.methods import CanUdsCommandService, CanUdsSleepMethod, CanUdsWakeMethod
from core.models import SleepMethodType, SuspendCycleRequest, WakeMethodType
from core.services import CycleRunnerService, ReportService, SuspendTestService


def _apply_cli_overrides(
    config,
    *,
    disable_serial_detector: bool,
    disable_adb_detector: bool,
    sleep_timeout: float | None,
    wake_timeout: float | None,
):
    serial_cfg = config.serial_detector
    adb_cfg = config.adb_detector
    timeouts = config.timeouts
    if disable_serial_detector:
        serial_cfg = replace(serial_cfg, enabled=False)
    if disable_adb_detector:
        adb_cfg = replace(adb_cfg, enabled=False)
    if sleep_timeout is not None:
        timeouts = replace(timeouts, sleep_timeout_seconds=sleep_timeout)
    if wake_timeout is not None:
        timeouts = replace(timeouts, wake_timeout_seconds=wake_timeout)
    return replace(
        config,
        serial_detector=serial_cfg,
        adb_detector=adb_cfg,
        timeouts=timeouts,
    )


def _build_services(config):
    command_service = CanUdsCommandService(config.can)
    sleep_method = CanUdsSleepMethod(command_service, config.sleep_can_uds)
    wake_method = CanUdsWakeMethod(command_service, config.wake_can_uds)

    detectors = []
    if config.serial_detector.enabled:
        detectors.append(SerialMcuSleepDetector(config.serial_detector))
    if config.adb_detector.enabled:
        detectors.append(AdbSocSleepDetector(config.adb_detector))

    suspend_service = SuspendTestService(sleep_method, wake_method, detectors)
    return CycleRunnerService(suspend_service), ReportService()


def _execute(
    *,
    cycles: int,
    config_path: Path,
    sleep_method: str,
    wake_method: str,
    disable_serial_detector: bool,
    disable_adb_detector: bool,
    sleep_timeout: float | None,
    wake_timeout: float | None,
    report_path: Path | None,
) -> Path:
    config_service = ConfigService()
    config = config_service.load(config_path)
    config = _apply_cli_overrides(
        config,
        disable_serial_detector=disable_serial_detector,
        disable_adb_detector=disable_adb_detector,
        sleep_timeout=sleep_timeout,
        wake_timeout=wake_timeout,
    )
    config_service.validate(config)

    if sleep_method != SleepMethodType.CAN_UDS.value:
        raise SuspendTestError(f"不支持的休眠方式: {sleep_method}")
    if wake_method != WakeMethodType.CAN_UDS.value:
        raise SuspendTestError(f"不支持的唤醒方式: {wake_method}")

    cycle_runner, report_service = _build_services(config)
    request = SuspendCycleRequest(
        cycles=cycles,
        sleep_timeout_seconds=config.timeouts.sleep_timeout_seconds,
        wake_timeout_seconds=config.timeouts.wake_timeout_seconds,
    )
    report = cycle_runner.run(request, config_path=config.config_path)
    return report_service.write_report(
        report,
        config_summary=config.summary(),
        output_path=report_path,
    )


def _handle_error(exc: Exception) -> None:
    if isinstance(exc, SuspendTestError):
        click.echo(f"错误: {exc}", err=True)
        if getattr(exc, "hint", None):
            click.echo(f"建议: {exc.hint}", err=True)
        raise click.Abort() from exc
    raise exc


def _common_options(func):
    func = click.option("--report", "report_path", type=click.Path(path_type=Path), default=None)(func)
    func = click.option("--wake-timeout", type=float, default=None)(func)
    func = click.option("--sleep-timeout", type=float, default=None)(func)
    func = click.option("--disable-adb-detector", is_flag=True, default=False)(func)
    func = click.option("--disable-serial-detector", is_flag=True, default=False)(func)
    func = click.option(
        "--wake-method",
        type=click.Choice([item.value for item in WakeMethodType]),
        default=WakeMethodType.CAN_UDS.value,
        show_default=True,
    )(func)
    func = click.option(
        "--sleep-method",
        type=click.Choice([item.value for item in SleepMethodType]),
        default=SleepMethodType.CAN_UDS.value,
        show_default=True,
    )(func)
    func = click.option(
        "--config",
        "config_path",
        type=click.Path(path_type=Path),
        default=Path("config.ini"),
        show_default=True,
    )(func)
    return func


@click.group(help="车机休眠/唤醒循环测试工具。")
def cli() -> None:
    """CLI 主命令。"""


@cli.command("run-once", help="执行一轮休眠/唤醒测试。")
@_common_options
def run_once(
    config_path: Path,
    sleep_method: str,
    wake_method: str,
    disable_serial_detector: bool,
    disable_adb_detector: bool,
    sleep_timeout: float | None,
    wake_timeout: float | None,
    report_path: Path | None,
) -> None:
    """执行单轮测试并输出报告。"""
    try:
        path = _execute(
            cycles=1,
            config_path=config_path,
            sleep_method=sleep_method,
            wake_method=wake_method,
            disable_serial_detector=disable_serial_detector,
            disable_adb_detector=disable_adb_detector,
            sleep_timeout=sleep_timeout,
            wake_timeout=wake_timeout,
            report_path=report_path,
        )
        click.echo(f"测试完成，报告已生成: {path}")
    except Exception as exc:  # noqa: BLE001
        _handle_error(exc)


@cli.command("loop", help="按指定轮次循环执行休眠/唤醒测试。")
@click.option("--cycles", type=int, required=True, help="循环次数。")
@_common_options
def loop(  # noqa: PLR0913
    cycles: int,
    config_path: Path,
    sleep_method: str,
    wake_method: str,
    disable_serial_detector: bool,
    disable_adb_detector: bool,
    sleep_timeout: float | None,
    wake_timeout: float | None,
    report_path: Path | None,
) -> None:
    """执行多轮循环测试并输出报告。"""
    try:
        path = _execute(
            cycles=cycles,
            config_path=config_path,
            sleep_method=sleep_method,
            wake_method=wake_method,
            disable_serial_detector=disable_serial_detector,
            disable_adb_detector=disable_adb_detector,
            sleep_timeout=sleep_timeout,
            wake_timeout=wake_timeout,
            report_path=report_path,
        )
        click.echo(f"循环测试完成，报告已生成: {path}")
    except Exception as exc:  # noqa: BLE001
        _handle_error(exc)


@cli.command("validate-config", help="校验配置文件格式是否正确。")
@click.option(
    "--config",
    "config_path",
    type=click.Path(path_type=Path),
    default=Path("config.ini"),
    show_default=True,
)
def validate_config(config_path: Path) -> None:
    """校验配置并输出摘要。"""
    try:
        config = ConfigService().load(config_path)
        click.echo("配置校验通过。")
        for key, value in sorted(config.summary().items()):
            click.echo(f"- {key}: {value}")
    except Exception as exc:  # noqa: BLE001
        _handle_error(exc)

