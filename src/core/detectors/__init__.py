"""检测器实现。"""

from core.detectors.adb_detector import AdbSocSleepDetector
from core.detectors.serial_detector import SerialMcuSleepDetector

__all__ = ["AdbSocSleepDetector", "SerialMcuSleepDetector"]

