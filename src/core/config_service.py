"""配置加载服务。"""

from __future__ import annotations

from configparser import ConfigParser, NoOptionError, NoSectionError
from pathlib import Path

from core.errors import ConfigError
from core.models import (
    AdbDetectorConfig,
    CanConfig,
    CanUdsMethodConfig,
    SerialDetectorConfig,
    SuspendTestConfig,
    TimeoutConfig,
)


class ConfigService:
    """配置加载与校验服务。"""

    def load(self, config_path: str | Path) -> SuspendTestConfig:
        """加载配置文件。

        Args:
            config_path: INI 文件路径。

        Returns:
            SuspendTestConfig: 强类型配置对象。
        """
        path = Path(config_path)
        if not path.exists():
            raise ConfigError(
                f"配置文件不存在: {path}",
                hint="请确认 config.ini 路径是否正确，或使用 --config 指定。",
            )

        parser = ConfigParser()
        parser.read(path, encoding="utf-8")

        can = self._load_can(parser)
        sleep_cfg = self._load_can_uds(parser, section="sleep.can_uds", default_id=can.physical_id)
        wake_cfg = self._load_can_uds(parser, section="wake.can_uds", default_id=can.physical_id)
        serial_cfg = self._load_serial_detector(parser)
        adb_cfg = self._load_adb_detector(parser)
        timeout_cfg = self._load_timeouts(parser)

        config = SuspendTestConfig(
            can=can,
            sleep_can_uds=sleep_cfg,
            wake_can_uds=wake_cfg,
            serial_detector=serial_cfg,
            adb_detector=adb_cfg,
            timeouts=timeout_cfg,
            config_path=path,
        )
        self.validate(config)
        return config

    def validate(self, config: SuspendTestConfig) -> None:
        """校验配置正确性。

        Args:
            config: 待校验配置。
        """
        if not (config.serial_detector.enabled or config.adb_detector.enabled):
            raise ConfigError(
                "至少需要启用一个检测器（串口或 ADB）。",
                hint="请在 [detect.serial] 或 [detect.adb] 中将 enabled 设为 true。",
            )

        for name, value in {
            "sleep request_id": config.sleep_can_uds.request_id,
            "wake request_id": config.wake_can_uds.request_id,
            "physical_id": config.can.physical_id,
            "response_id": config.can.response_id,
            "functional_id": config.can.functional_id,
        }.items():
            if not (0 <= value <= 0x7FF):
                raise ConfigError(
                    f"{name} 超出标准 CAN ID 范围: {value:#x}",
                    hint="请使用 0x000 到 0x7FF 之间的标准 ID。",
                )

        for name, payload in {
            "sleep request_data": config.sleep_can_uds.request_data,
            "wake request_data": config.wake_can_uds.request_data,
        }.items():
            if not payload:
                raise ConfigError(f"{name} 不能为空。")
            if len(payload) > 8:
                raise ConfigError(
                    f"{name} 长度为 {len(payload)}，超过标准 CAN 单帧 8 字节。",
                    hint="当前版本仅支持单帧发送，请缩短数据长度。",
                )

        if config.timeouts.sleep_timeout_seconds <= 0 or config.timeouts.wake_timeout_seconds <= 0:
            raise ConfigError("休眠/唤醒超时必须为正数。")

        if config.can.channel < 0:
            raise ConfigError("can.channel 不能小于 0。")

        if config.can.device_index < 0:
            raise ConfigError("can.device_index 不能小于 0。")

    def _load_can(self, parser: ConfigParser) -> CanConfig:
        return CanConfig(
            interface=parser.get("can", "interface", fallback="zlgcan").strip(),
            channel=parser.getint("can", "channel", fallback=0),
            bitrate=parser.getint("can", "bitrate", fallback=500000),
            device_type=parser.get("can", "device_type", fallback="ZCAN_USBCANFD_200U").strip(),
            device_index=parser.getint("can", "device_index", fallback=0),
            libpath=parser.get("can", "libpath", fallback="library/").strip(),
            resistance=parser.getboolean("can", "resistance", fallback=True),
            physical_id=self._parse_int(parser.get("can", "physical_id", fallback="0x773")),
            response_id=self._parse_int(parser.get("can", "response_id", fallback="0x7B3")),
            functional_id=self._parse_int(parser.get("can", "functional_id", fallback="0x7DF")),
        )

    def _load_can_uds(self, parser: ConfigParser, *, section: str, default_id: int) -> CanUdsMethodConfig:
        request_id = self._parse_int(parser.get(section, "request_id", fallback=f"0x{default_id:X}"))
        request_data = self._parse_bytes(self._must_get(parser, section, "request_data"))
        return CanUdsMethodConfig(request_id=request_id, request_data=request_data)

    def _load_serial_detector(self, parser: ConfigParser) -> SerialDetectorConfig:
        return SerialDetectorConfig(
            enabled=parser.getboolean("detect.serial", "enabled", fallback=True),
            port=parser.get("detect.serial", "port", fallback="/dev/ttyUSB0"),
            baudrate=parser.getint("detect.serial", "baudrate", fallback=115200),
            silence_seconds=parser.getfloat("detect.serial", "silence_seconds", fallback=0.5),
            poll_interval_seconds=parser.getfloat("detect.serial", "poll_interval_seconds", fallback=0.05),
        )

    def _load_adb_detector(self, parser: ConfigParser) -> AdbDetectorConfig:
        serial = parser.get("detect.adb", "device_serial", fallback="").strip() or None
        return AdbDetectorConfig(
            enabled=parser.getboolean("detect.adb", "enabled", fallback=True),
            adb_path=parser.get("detect.adb", "adb_path", fallback="adb"),
            device_serial=serial,
            poll_interval_seconds=parser.getfloat("detect.adb", "poll_interval_seconds", fallback=0.5),
            command_timeout_seconds=parser.getfloat("detect.adb", "command_timeout_seconds", fallback=3.0),
        )

    def _load_timeouts(self, parser: ConfigParser) -> TimeoutConfig:
        return TimeoutConfig(
            sleep_timeout_seconds=parser.getfloat("timeouts", "sleep_timeout_seconds", fallback=30.0),
            wake_timeout_seconds=parser.getfloat("timeouts", "wake_timeout_seconds", fallback=30.0),
        )

    @staticmethod
    def _parse_int(raw: str) -> int:
        text = raw.strip().lower()
        base = 16 if text.startswith("0x") else 10
        return int(text, base)

    @staticmethod
    def _parse_bytes(raw: str) -> bytes:
        parts = [chunk.strip() for chunk in raw.replace(",", " ").split() if chunk.strip()]
        if not parts:
            raise ConfigError("request_data 不能为空。")
        byte_values = []
        for part in parts:
            text = part.lower()
            value = int(text, 16) if text.startswith("0x") else int(text, 16)
            if not (0 <= value <= 0xFF):
                raise ConfigError(f"request_data 字节超范围: {part}")
            byte_values.append(value)
        return bytes(byte_values)

    @staticmethod
    def _must_get(parser: ConfigParser, section: str, option: str) -> str:
        try:
            return parser.get(section, option)
        except (NoSectionError, NoOptionError) as exc:
            raise ConfigError(
                f"配置缺失: [{section}] {option}",
                hint="请参考默认 config.ini 填写完整字段。",
            ) from exc
