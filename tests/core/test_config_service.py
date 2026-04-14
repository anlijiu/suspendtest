"""ConfigService 测试。"""

from __future__ import annotations

from pathlib import Path

import pytest

from core.config_service import ConfigService
from core.errors import ConfigError


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


def test_load_config_success(tmp_path: Path) -> None:
    config_file = tmp_path / "config.ini"
    _write_default_config(config_file)

    config = ConfigService().load(config_file)

    assert config.can.physical_id == 0x773
    assert config.sleep_can_uds.request_data == bytes([0x10, 0x01])
    assert config.serial_detector.enabled is True
    assert config.adb_detector.enabled is True


def test_load_config_missing_required_field(tmp_path: Path) -> None:
    config_file = tmp_path / "config.ini"
    config_file.write_text(
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

[wake.can_uds]
request_id = 0x773
request_data = 11 01
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="配置缺失"):
        ConfigService().load(config_file)


def test_validate_reject_when_all_detectors_disabled(tmp_path: Path) -> None:
    config_file = tmp_path / "config.ini"
    _write_default_config(config_file)
    config = ConfigService().load(config_file)
    config.serial_detector.enabled = False
    config.adb_detector.enabled = False

    with pytest.raises(ConfigError, match="至少需要启用一个检测器"):
        ConfigService().validate(config)

