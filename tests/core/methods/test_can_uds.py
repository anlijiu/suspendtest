"""CanUdsCommandService 测试。"""

from __future__ import annotations

from dataclasses import dataclass

from core.methods.can_uds import CanUdsCommandService
from core.models import CanConfig


@dataclass(slots=True)
class _FakeBus:
    sent_messages: list[object]

    def send(self, message: object) -> None:
        self.sent_messages.append(message)

    def shutdown(self) -> None:
        return None


def test_send_uses_zlgcan_bus_kwargs() -> None:
    captured_kwargs: dict[str, object] = {}
    sent_messages: list[object] = []

    def fake_bus_factory(**kwargs: object) -> _FakeBus:
        nonlocal captured_kwargs
        captured_kwargs = kwargs
        return _FakeBus(sent_messages=sent_messages)

    can_config = CanConfig(
        interface="zlgcan",
        channel=0,
        bitrate=500000,
        device_type="ZCAN_USBCANFD_200U",
        device_index=0,
        libpath="library/",
        resistance=True,
        physical_id=0x773,
        response_id=0x7B3,
        functional_id=0x7DF,
    )

    result = CanUdsCommandService(
        can_config,
        bus_factory=fake_bus_factory,
    ).send("can_uds_sleep", request_id=0x773, request_data=bytes([0x10, 0x01]))

    assert result.success is True
    assert captured_kwargs["interface"] == "zlgcan"
    assert captured_kwargs["channel"] == 0
    assert captured_kwargs["device_index"] == 0
    assert isinstance(captured_kwargs["configs"], list)
    assert len(sent_messages) == 1

